# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from itertools import groupby
from odoo.exceptions import MissingError, ValidationError, AccessError

from odoo import api,fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta, date
from odoo.fields import Command
import re
import itertools
import pytz

READONLY_FIELD_STATES = {
	state: [('readonly', True)]
	for state in {'sale', 'done', 'cancel'}
}

ORDER_LINE_FIELDS = ['product_uom_qty','price_unit','price_subtotal','tax_id']


class ProductVendorConf(models.Model):
	_name = "product.vendor.conf"
	_description = "Product Vendor Conf"

	product_id = fields.Many2one('product.product',string="Product")
	partner_id = fields.Many2one('res.partner',string="Vendor")
	sale_id = fields.Many2one('sale.order',string="Order")
	sale_line_id = fields.Many2one('sale.order.line',string="Sale Order Line")
	supplier_info_id = fields.Many2one('product.supplierinfo')
	bom_line_id = fields.Many2one('mrp.bom.line')


class SaleOrder(models.Model):
	_inherit = "sale.order"

	# attn_to = fields.Char('Attn To', related="partner_id.attn_to")
	type = fields.Selection([
		('sale', 'Sale Order'),
		('loan', 'Loan Order'),
		('exchange', 'Exchange Order'),
		('training', 'Training'),
		('replacement', 'Replacement Order')
	], default='sale')
	loan_state = fields.Selection([
		('open', 'Open'),
		('closed', 'Closed'),
		('not_loan', 'Not Loan')
	], compute="_compute_loan_state", store=True)
	loan_date = fields.Date('Loan Date', compute="_compute_loan_state", store=True)
	billing_state = fields.Selection([
		('open', 'Open'),
		('closed', 'Closed'),
		('no_invoice','No Invoice')
	], compute="_compute_billing_state")
	sale_id = fields.Many2one('sale.order', 'Sale')
	# exchange_order_ids = fields.One2many('sale.order', 'sale_id', string="Exchange Order")
	# exchange_order_count = fields.Integer('Exchange Order Count', compute="_compute_exchange_order_ids")
	loan_ids = fields.One2many('sale.order','sale_id',string="Loan Order")
	loan_order_count = fields.Integer('Loan Order Count', compute="_compute_loan_ids")
	# replacement_order_ids = fields.One2many('sale.order', 'sale_id', string="Replacement Order")
	# replacement_order_count = fields.Integer('Replacement Order Count', compute="_compute_replacement_order_ids")
	partner_invoice_address = fields.Char()
	check_partner_address = fields.Boolean('Check Partner Address', default=False)
	customer_code = fields.Char('Customer Code', related="partner_id.customer_code")
	terms_and_conditions = fields.Html('Terms and Conditions', compute="_get_terms_and_conditions")
	purchase_ref = fields.Char('Purchase Reference', compute="_compute_purchase_ref", store=True)
	journal_id = fields.Many2one('account.journal', 'Billing Mode')
	user = fields.Many2one('res.users', default=lambda self: self.env.user)
	today = fields.Datetime(string='Singapore Date & Time', default=datetime.now(), tz='Asia/Indonesia')
	len_note = fields.Char('Length Internal Notee', compute="_compute_sale_internal_note", store=True)
	partner_note = fields.Text('Note')
	delivery_type = fields.Selection([
		('self_collection', 'Self Collection'),
		('in_house_driver', 'Delivery by In-house Driver'),
		('third_party_logistics','Delivery by Third-party Logistics')
	], default='self_collection')
	route_id = fields.Many2one('fischerbell.delivery.route', 'Delivery Route')
	approval_state = fields.Selection(
		selection=[
			('no', 'Nothing To Approve'),
			('approved', 'Approved'),
			('waiting_approval', 'Waiting Approval'),
			('reject', 'Rejected')
		],
		string="Approval Status", default='no', tracking=True)
	is_approved = fields.Boolean('Is Approved')
	state = fields.Selection(
		selection=[
			('draft', "Quotation"),
			('sent', "Quotation Sent"),
			('sale', "Sales Order"),
			('done', "Locked"),
			('cancel', "Cancelled"),
			('waiting_approval', 'Waiting Approval'),
		],
		string="Status",
		readonly=True, copy=True, index=True,
		tracking=3,
		default='draft')

	contact_person_id = fields.Many2one('res.partner', string='Contact Person')
	contact_person_comp_id = fields.Many2one('res.partner', string='Contact Person Company',compute="_get_contact_person_company")
	# contact_person_comp_id = fields.Many2one('res.partner', string='Contact Person Company',related="contact_person_id.parent_id")
	contact_per_name = fields.Char(string="Contact Person Name",readonly=True)
	revision_order_count = fields.Float(sting="Revision Order Count",default=1.0)
	revision_order_name = fields.Char(sting="Revision Order Name")
	is_order_revise = fields.Boolean(default=False)
	reviewed_by = fields.Many2one("res.users",string="Reviewed By")
	email_to_customer = fields.Datetime(string="Email To Customer")
	first_followup_date = fields.Datetime(string="First Follow Up")
	sec_followup_date = fields.Datetime(string="Sec Follow Up")
	scheduled_delivery_date = fields.Datetime(string="Scheduled Delivery Date")
	requested_delivery_date = fields.Datetime(string="Requested Delivery Date")
	no_enough_stock = fields.Boolean(compute='_compute_order_stock')
	over_credit_limit = fields.Boolean(compute='_compute_credit_limit', store=True)
	submited_date = fields.Date('Submited Date')
	artwork_attachment_ids = fields.Many2many('ir.attachment',string="ArtWork")
	delivery_instruction = fields.Html(string="Delivery Instruction")
	invoice_instruction = fields.Html(string="Invoice Instruction")
	delivery_option = fields.Selection(
		selection=[('partial_delivery', 'Partial Delivery'),
			('full_delivery', 'Wait for the receival of all goods')],
		string="Delivery Option", default='partial_delivery')

	product_vendor_conf_ids = fields.One2many('product.vendor.conf','sale_id',string="Product Vendor Conf")


	@api.depends('partner_id')
	def _compute_partner_shipping_id(self):
		for order in self:
			order.partner_shipping_id = order.partner_id.address_get(['delivery'])['delivery'] if order.partner_id else False
			order.route_id = order.get_route_id(order.partner_shipping_id)


	def get_route_id(self, partner_shipping_id):
		if partner_shipping_id and partner_shipping_id.zip:
			postal_code = '{:.2}'.format(partner_shipping_id.zip)
			zip_number = self.env['fischerbell.delivery.route.line'].search([('name','=',postal_code)], limit=1)
			return zip_number.route_id.id if zip_number else False
		else:
			return False

	def _compute_order_stock(self):
		for order in self:
			order.no_enough_stock = True
			no_stock = any(line.product_uom_qty > line.product_template_id.qty_available for line in order.order_line)
			if no_stock:
				order.no_enough_stock = False

	@api.depends('partner_id', 'amount_total')
	def _compute_credit_limit(self):
		for order in self:
			order.over_credit_limit = False
			if order.amount_total > order.partner_id.credit_limit and order.partner_id.credit_limit != 0:
				order.over_credit_limit = True


	@api.onchange('scheduled_delivery_date')
	def _onchange_partner_not_avalibale(self):
		partner = self.partner_id.parent_id if self.partner_id.parent_id else self.partner_id
		if partner.no_delivery_days_selection == 'days' and int(partner.no_delivery_days) == self.scheduled_delivery_date.weekday():
			raise ValidationError("Customer is not available during this date")
		if partner.no_delivery_days_selection == 'date' and partner.delivery_restriction_start_date <= self.scheduled_delivery_date.date() <= partner.delivery_restriction_end_date:
			raise ValidationError(f"Customer is not available from {partner.delivery_restriction_start_date.strftime('%d-%m-%Y')} to {partner.delivery_restriction_end_date.strftime('%d-%m-%Y')}")
		# if self.partner_id.parent_id:
		# 	if self.partner_id.parent_id.no_delivery_days_selection == 'days':
		# 		if int(self.partner_id.parent_id.no_delivery_days) == self.scheduled_delivery_date.weekday():
		# 			raise ValidationError("Customer is not avaliable during this date")
		# 	if self.partner_id.parent_id.no_delivery_days_selection == 'date':
		# 		if self.partner_id.parent_id.delivery_restriction_start_date <= self.scheduled_delivery_date.date() <= self.partner_id.parent_id.delivery_restriction_end_date:
		# 			raise ValidationError(f"Customer is not avaliable from {self.partner_id.parent_id.delivery_restriction_start_date} to {self.partner_id.parent_id.delivery_restriction_end_date}")
		# else:
		# 	if self.partner_id.no_delivery_days_selection == 'days':
		# 		if int(self.partner_id.no_delivery_days) == self.scheduled_delivery_date.weekday():
		# 			raise ValidationError("Customer is not avaliable during this date")
		# 	if self.partner_id.no_delivery_days_selection == 'date':
		# 		if self.partner_id.delivery_restriction_start_date <= self.scheduled_delivery_date.date() <= self.partner_id.delivery_restriction_end_date:
		# 			raise ValidationError(f"Customer is not avaliable from {self.partner_id.delivery_restriction_start_date} to {self.partner_id.delivery_restriction_end_date}")


	@api.onchange('contact_person_id')
	def _onchange_set_customer(self):
		for rec in self:
			# if not rec.partner_id:
			rec.partner_id = rec.contact_person_id.id

	def _get_contact_person_company(self):
		for rec in self:
			if rec.contact_person_id:
				rec.contact_person_comp_id = rec.contact_person_id.parent_id.id
				rec.contact_per_name = rec.contact_person_id.name
			else:
				rec.contact_person_comp_id = False

	def _update_approval_state(self):
		orders = self.env['sale.order'].search([('approval_state','=','no')])
		for order in orders:
			if order.state == 'draft':
				order.approval_state = 'no'
			if order.state == 'sale' and order.picking_ids:
				order.approval_state = 'approved'
			if order.state == 'cancel':
				order.approval_state = 'reject'



	# def action_to_approve(self):
	# 	for order in self:
	# 		if any(line.product_uom_qty > line.product_id.qty_available for line in order.order_line):
	# 			# if order.state == 'waiting_approval' and order.approval_state == 'waiting_approval' and self.env.user.has_group("fischerbell_custom.group_sales_order_approver"):
	# 			# 	order.write({
	# 			# 		'state': 'sale',
	# 			# 		'approval_state': 'approved'
	# 			# 	})
	# 			return {
	# 				'name': "Product Avaliable",
	# 				'type': 'ir.actions.act_window',
	# 				'view_type': 'form',
	# 				'view_mode': 'form',
	# 				'res_model': 'avaliable.product.qty',
	# 				'view_id': self.env.ref('fischerbell_custom.avaliable_product_qty_form_view').id,
	# 				'target': 'new'
	# 			}
	# 			# order.action_confirm()
	# 			# else:
	# 			# 	raise ValidationError("Sorry, you are not allowed to approve this order.")
	# 		else:
	# 			if order.state == 'waiting_approval' and order.approval_state == 'waiting_approval' and self.env.user.has_group("fischerbell_custom.group_sales_order_approver"):
	# 				order.write({
	# 					'state': 'sale',
	# 					'approval_state': 'approved',
	# 					'reviewed_by': self.env.user.id
	# 				})
	# 				order.action_confirm()
	# 			else:
	# 				raise ValidationError("Sorry, you are not allowed to approve this order.")
	# 	return True


	# @api.model_create_multi
	# def create(self, vals_list):
	# 	for vals in vals_list:
	# 		if 'partner_seq' not in vals or vals['partner_seq'] == _('New'):
	# 			vals['partner_seq'] = self.env['ir.sequence'].next_by_code('quality.point') or _('New')
	# 	return super().create(vals_list)
	def action_to_approve(self):
		for order in self:
			# if order.partner_id.credit_limit > 0:
			if order.amount_total < order.partner_id.credit_limit:
				if order.state == 'waiting_approval' and order.approval_state == 'waiting_approval' and self.env.user.has_group(
						"fischerbell_custom.group_sales_order_approver"):
					order.write({
						'state': 'sale',
						'approval_state': 'approved',
						'reviewed_by': self.env.user.id
					})
					if order.partner_id.partner_seq == _('New'):
						partner = self.env['res.partner'].browse(order.partner_id.id)
						partner.update({
							'partner_seq': self.env['ir.sequence'].next_by_code('res.partner') or _('New')
						})
					order.with_context(vendor_wizard=True).action_confirm()
					purchase_order_ids = self._get_purchase_orders()
					if purchase_order_ids:
						purchase_id = purchase_order_ids[0]
						return {
							'name': "Low Stock Alert",
							'type': 'ir.actions.act_window',
							'view_type': 'form',
							'view_mode': 'form',
							'res_model': 'purchase.order.ref',
							'context': {
								'default_name': f"Sale order - {order.name} has some products which are having low stock, please find the details below:\n{','.join(purchase_id.order_line.mapped('product_id.name'))}\nPurchase Order Ref: {purchase_id.name}"
							},
							'view_id': self.env.ref('fischerbell_custom.purchase_order_ref_form_view').id,
							'target': 'new'
						}
					not_enough_stock = any(
						line.product_uom_qty > line.product_id.qty_available for line in order.order_line)
					if order.partner_id.credit_limit > 0:
						return {'warning': {
							'title': _("Warning"),
							'message': "Customer exceeded the credit limit"
						}}
					if not_enough_stock:
						pass
				else:
					raise ValidationError("Sorry, you are not allowed to approve this order.")
				# else:
				# 	raise ValidationError("Customer exceeded the credit limit.")
			else:
				if order.state == 'waiting_approval' and order.approval_state == 'waiting_approval' and self.env.user.has_group(
						"fischerbell_custom.group_sales_order_approver"):
					order.write({
						'state': 'sale',
						'approval_state': 'approved',
						'reviewed_by': self.env.user.id
					})
					if order.partner_id.partner_seq == _('New'):
						partner = self.env['res.partner'].browse(order.partner_id.id)
						partner.update({
							'partner_seq': self.env['ir.sequence'].next_by_code('res.partner') or _('New')
						})
					order.with_context(vendor_wizard=True).action_confirm()
					purchase_order_ids = self._get_purchase_orders()
					if purchase_order_ids:
						purchase_id = purchase_order_ids[0]
						return {
							'name': "Low Stock Alert",
							'type': 'ir.actions.act_window',
							'view_type': 'form',
							'view_mode': 'form',
							'res_model': 'purchase.order.ref',
							'context': {
								'default_name': f"Sale order - {order.name} has some products which are having low stock, please find the details below:\n{','.join(purchase_id.order_line.mapped('product_id.name'))}\nPurchase Order Ref: {purchase_id.name}"
							},
							'view_id': self.env.ref('fischerbell_custom.purchase_order_ref_form_view').id,
							'target': 'new'
						}
					not_enough_stock = any(
						line.product_uom_qty > line.product_id.qty_available for line in order.order_line)
					if order.partner_id.credit_limit > 0:
						return {'warning': {
							'title': _("Warning"),
							'message': "Customer exceeded the credit limit"
						}}
					if not_enough_stock:
						pass
				else:
					raise ValidationError("Sorry, you are not allowed to approve this order.")
		return True

	def action_stock_confirm(self):
		self.ensure_one()
		outgoing_delivery_ids = self.picking_ids.filtered(lambda delivery: delivery.picking_type_code == 'outgoing')
		for delivery in outgoing_delivery_ids:
			delivery.enough_stock = False

	def action_to_reject(self):
		for order in self:
			if order.state == 'waiting_approval' and order.approval_state == 'waiting_approval' and self.env.user.has_group("fischerbell_custom.group_sales_order_approver"):
				order.write({
					'state': 'cancel',
					'approval_state': 'reject',
					'reviewed_by': self.env.user.id
				})
			elif order.state == 'waiting_approval_user' and order.approval_state == 'waiting_approval' and self.env.user.has_group("fischerbell_custom.group_sales_order_approver"):
				order.write({
					'state': 'cancel',
					'approval_state': 'reject',
					'reviewed_by': self.env.user.id
				})
			else:
				raise ValidationError("Sorry, you are not allowed to reject this order.")

		return True

	@api.depends('partner_note')
	def _compute_sale_internal_note(self):
		self.len_note = False
		for inv in self:
			if inv.partner_note:
				inv.len_note = len(inv.partner_note)
			else:
				inv.len_note = False

	# def action_confirm(self):
	# 	self.submited_date = date.today()
	# 	for rec in self.order_line:
	# 		# line_ids = self.order_line.filtered(lambda line:not line.product_template_id.seller_ids)
	# 		if not rec.product_template_id.seller_ids and not self._context.get('vendor_wizard'):
	# 			return {'type': 'ir.actions.act_window',
	# 			        'name': _('Product wizard'),
	# 			        'res_model': 'update.product.vendor',
	# 			        'view_mode': 'form',
	# 			        # 'context': {'order_id': self.id,'line_ids':line_ids},
	# 			        'target': 'new',
	# 			        }
	# 	super_call = super(SaleOrder, self).action_confirm()
	# 	for order in self:
	# 		# Sent email to customer based on the state
	# 		order.send_mail_triggers_based_on_state()
	# 	return super_call


	def action_confirm(self):
		self.submited_date = date.today()
		if not 'vendor_wizard' in self._context:
			line_ids = []
			for rec in self.order_line:
				line = rec
				mrp_route_id = self.env.ref('purchase_stock.route_warehouse0_buy')
				mto_route_id = self.env.ref('stock.route_warehouse0_mto')
				if mrp_route_id and mto_route_id and (mrp_route_id in line.product_id.route_ids) or (mto_route_id in line.product_id.route_ids) and line.product_id.bom_ids:
					boms = line.product_id.bom_ids._bom_find(line.product_id, company_id=line.company_id.id, bom_type='phantom')[line.product_id]
					if boms:
						for bom_line in boms[0].bom_line_ids:
							line_ids.append((0,0,{'product_id':bom_line.product_id.id,'demand_qty':rec.product_uom_qty,'sale_line_id':line.id,'bom_line_id':bom_line.id}))
				if not rec.product_id.product_tmpl_id.seller_ids:
					line_ids.append((0,0,{'product_id':bom_line.product_id.id,'demand_qty':rec.product_uom_qty,'sale_line_id':line.id}))
			if line_ids:
				return {'type': 'ir.actions.act_window',
						'name': _('Product wizard'),
						'res_model': 'update.product.vendor',
						'view_mode': 'form',
						'context': {'order_id': self.id,'line_ids':line_ids},
						'target': 'new',
						}
			else:
				return super(SaleOrder, self).action_confirm()
				
		super_call = super(SaleOrder, self).action_confirm()
		for order in self:
			order.send_mail_triggers_based_on_state()
		return super_call


	def update_vendor(self):
		self.submited_date = date.today()
		line_ids = []
		for rec in self.order_line:
			line = rec
			mrp_route_id = self.env.ref('purchase_stock.route_warehouse0_buy')
			mto_route_id = self.env.ref('stock.route_warehouse0_mto')
			if mrp_route_id and mto_route_id and (mrp_route_id in line.product_id.route_ids) or (mto_route_id in line.product_id.route_ids) and line.product_id.bom_ids:
				boms = line.product_id.bom_ids._bom_find(line.product_id, company_id=line.company_id.id, bom_type='phantom')[line.product_id]
				if boms:
					for bom_line in boms[0].bom_line_ids:
						line_ids.append((0,0,{'product_id':bom_line.product_id.id,'demand_qty':rec.product_uom_qty}))
			if not rec.product_id.product_tmpl_id.seller_ids:
				line_ids.append((0,0,{'product_id':bom_line.product_id.id,'demand_qty':rec.product_uom_qty}))
		if line_ids:
			return {'type': 'ir.actions.act_window',
					'name': _('Product wizard'),
					'res_model': 'update.product.vendor',
					'view_mode': 'form',
					'context': {'order_id': self.id,'line_ids':line_ids},
					'target': 'new',
					}


	# def action_confirm(self):
	# 	res = super().action_confirm()
	# 	mrp_list = []
	# 	for order in self:
	# 		if order.state == 'sale' and order.approval_state == 'approved':
	# 			manufacture_obj = self.env['mrp.production']
	# 			for line in order.order_line:
	# 				if line.product_template_id.bom_ids:
	# 					for bom in line.product_template_id.bom_ids:
	# 						if bom.type == 'phantom':
	# 							procurement = self.env['procurement.group'].search([('name','=',order.name)], limit=1)
	# 							if not procurement:
	# 								procurement = self.env['procurement.group'].create({'name': order.name, 'move_type': 'direct'})
	# 							mrp = self.env['mrp.production'].create({
	# 								'product_id': line.product_id.id,
	# 								'sale_id': order.id,
	# 								'procurement_group_id': procurement.id,
	# 								'product_qty': line.product_uom_qty,
	# 								'bom_id': bom.id,
	# 							})
	# 							mrp_list.append(mrp.id)
	# 								# for bom_line in bom.bom_line_ids:
	# 								# 	mrp_line = self.env['stock.move'].create({
	# 								# 			'product_id': bom_line.product_id.id,
	# 								# 			'raw_material_production_id': mrp.id,
	# 								# 			'product_uom_qty': bom_line.product_qty * line.product_uom_qty,
	# 								# 			'warehouse_id': order.warehouse_id.id,
	# 								# 			# 'bom_line_id': bom_line.id
	# 								# 		})

	# 						else:
	# 							pass
	# 				else:
	# 					pass

	# 		if order.picking_ids:
	# 			for pick in order.picking_ids:
	# 				pick.user = self.env.user.id

	# 	mrp_production_ids = self.env['mrp.production'].search([('id','in',mrp_list)])
	# 	if mrp_production_ids:
	# 		self.mrp_production_ids = mrp_production_ids

	# 	for order in self:
	# 		productions = self.env['mrp.production'].search([('origin','=',order.name),('sale_id','=',False)])
	# 		for production in productions:
	# 			production.write({'sale_id': order.id})

	# 	return res

	@api.onchange('partner_id','type')
	def _onchange_trainer_desc(self):
		for order in self:
			if order.partner_id.user_training_ids and order.type == 'training':
				product = self.env['product.product'].sudo().search([('type','not in',['service','product']),('categ_id.is_training','=',True)], limit=1)
				if product:
					for trainer in order.partner_id.user_training_ids:
						description = ''
						description_sale = ''
						trainer_name = ''
						trainer_datetime = ''
						trainer_venue = ''
						trainer_type = ''
						trainer_desc = ''
						if trainer.name:
							trainer_name = f"Trainer Name : {trainer.name}"
						if trainer.datetime:
							trainer_datetime = f"Trainer Date : {trainer.datetime.strftime('%d/%m/%Y')}\nTrainer Time : {trainer.datetime.strftime('%H:%M:%S')}"
						if trainer.venue:
							trainer_venue = f"Trainer Venue : {trainer.venue}"
						if trainer.type:
							trainer_type = f"Trainer Type : {trainer.type}"
						if product.description_sale:
							description_sale = f"{product.description_sale}"

						trainer_desc = f"{trainer_name}\n{trainer_datetime}\n{trainer_venue}\n{trainer_type}"
						if description_sale:
							description += description_sale + '\n' + trainer_desc
						else:
							description += trainer_desc
						self.update({'order_line': [(0,0,{'product_template_id': product.product_tmpl_id.id, 'product_id': product.id, 'name': description, 'product_uom_qty': 1})]})
				else:
					pass
					# line[0].update({'name': 'state no. of trainess : '})
			else:
				self.update({'order_line': False})

			if order.partner_id:
				config_note = self.env['fischerbell.configuration.note'].search([
					('type', '=', 'sale'),
					('partner_ids', 'in', [order.partner_id.id])  # Use a list to compare with a Many2many field
				], limit=1)
				order.partner_note = config_note.note


	def _create_invoices(self, grouped=False, final=False, date=None):
		""" Create invoice(s) for the given Sales Order(s).

		:param bool grouped: if True, invoices are grouped by SO id.
			If False, invoices are grouped by keys returned by :meth:`_get_invoice_grouping_keys`
		:param bool final: if True, refunds will be generated if necessary
		:param date: unused parameter
		:returns: created invoices
		:rtype: `account.move` recordset
		:raises: UserError if one of the orders has no invoiceable lines.
		"""
		if not self.env['account.move'].check_access_rights('create', False):
			try:
				self.check_access_rights('write')
				self.check_access_rule('write')
			except AccessError:
				return self.env['account.move']

		# 1) Create invoices.
		invoice_vals_list = []
		invoice_item_sequence = 0 # Incremental sequencing to keep the lines order on the invoice.
		for order in self:
			if order.type == 'loan':
				for pick in order.picking_ids:
					if pick.is_return_loan:
						pick.write({'state': 'cancel'})

			order = order.with_company(order.company_id).with_context(lang=order.partner_invoice_id.lang)

			invoice_vals = order._prepare_invoice()
			invoice_vals['narration'] = f"{'Terms and Conditions :'}"
			invoiceable_lines = order._get_invoiceable_lines(final)

			if not any(not line.display_type for line in invoiceable_lines):
				continue

			invoice_line_vals = []
			down_payment_section_added = False
			for line in invoiceable_lines:
				if not down_payment_section_added and line.is_downpayment:
					# Create a dedicated section for the down payments
					# (put at the end of the invoiceable_lines)
					invoice_line_vals.append(
						Command.create(
							order._prepare_down_payment_section_line(sequence=invoice_item_sequence)
						),
					)
					down_payment_section_added = True
					invoice_item_sequence += 1
				invoice_line_vals.append(
					Command.create(
						line._prepare_invoice_line(sequence=invoice_item_sequence)
					),
				)
				invoice_item_sequence += 1

			invoice_vals['invoice_line_ids'] += invoice_line_vals
			invoice_vals_list.append(invoice_vals)

		if not invoice_vals_list and self._context.get('raise_if_nothing_to_invoice', True):
			raise UserError(self._nothing_to_invoice_error_message())

		# 2) Manage 'grouped' parameter: group by (partner_id, currency_id).
		if not grouped:
			new_invoice_vals_list = []
			invoice_grouping_keys = self._get_invoice_grouping_keys()
			invoice_vals_list = sorted(
				invoice_vals_list,
				key=lambda x: [
					x.get(grouping_key) for grouping_key in invoice_grouping_keys
				]
			)
			for _grouping_keys, invoices in groupby(invoice_vals_list, key=lambda x: [x.get(grouping_key) for grouping_key in invoice_grouping_keys]):
				origins = set()
				payment_refs = set()
				refs = set()
				ref_invoice_vals = None
				for invoice_vals in invoices:
					if not ref_invoice_vals:
						ref_invoice_vals = invoice_vals
					else:
						ref_invoice_vals['invoice_line_ids'] += invoice_vals['invoice_line_ids']
					origins.add(invoice_vals['invoice_origin'])
					payment_refs.add(invoice_vals['payment_reference'])
					refs.add(invoice_vals['ref'])
				ref_invoice_vals.update({
					'ref': ', '.join(refs)[:2000],
					'invoice_origin': ', '.join(origins),
					'payment_reference': len(payment_refs) == 1 and payment_refs.pop() or False,
				})
				new_invoice_vals_list.append(ref_invoice_vals)
			invoice_vals_list = new_invoice_vals_list

		# 3) Create invoices.

		# As part of the invoice creation, we make sure the sequence of multiple SO do not interfere
		# in a single invoice. Example:
		# SO 1:
		# - Section A (sequence: 10)
		# - Product A (sequence: 11)
		# SO 2:
		# - Section B (sequence: 10)
		# - Product B (sequence: 11)
		#
		# If SO 1 & 2 are grouped in the same invoice, the result will be:
		# - Section A (sequence: 10)
		# - Section B (sequence: 10)
		# - Product A (sequence: 11)
		# - Product B (sequence: 11)
		#
		# Resequencing should be safe, however we resequence only if there are less invoices than
		# orders, meaning a grouping might have been done. This could also mean that only a part
		# of the selected SO are invoiceable, but resequencing in this case shouldn't be an issue.
		if len(invoice_vals_list) < len(self):
			SaleOrderLine = self.env['sale.order.line']
			for invoice in invoice_vals_list:
				sequence = 1
				for line in invoice['invoice_line_ids']:
					line[2]['sequence'] = SaleOrderLine._get_invoice_line_sequence(new=sequence, old=line[2]['sequence'])
					sequence += 1

		# Manage the creation of invoices in sudo because a salesperson must be able to generate an invoice from a
		# sale order without "billing" access rights. However, he should not be able to create an invoice from scratch.
		moves = self.env['account.move'].sudo().with_context(default_move_type='out_invoice').create(invoice_vals_list)

		# 4) Some moves might actually be refunds: convert them if the total amount is negative
		# We do this after the moves have been created since we need taxes, etc. to know if the total
		# is actually negative or not
		if final:
			moves.sudo().filtered(lambda m: m.amount_total < 0).action_switch_invoice_into_refund_credit_note()
		for move in moves:
			move.message_post_with_view(
				'mail.message_origin_link',
				values={'self': move, 'origin': move.line_ids.sale_line_ids.order_id},
				subtype_id=self.env['ir.model.data']._xmlid_to_res_id('mail.mt_note'))
		return moves


	@api.depends('purchase_order_count')
	def _compute_purchase_ref(self):
		self.purchase_ref = ''
		for order in self:
			purchase_order_line = self.env['purchase.order.line'].search([('sale_id','=',order.id)])
			if purchase_order_line:
				for po_line in purchase_order_line:
					order.purchase_ref = po_line.order_id.name + ', '
			else:
				order.purchase_ref = ''

	def _get_terms_and_conditions(self):
		quo_terms = self.env['fischerbell.sale.terms.and.conditions'].search([('type','=','quotation')], limit=1)
		for order in self:
			if order.state == 'draft':
				order.terms_and_conditions = quo_terms.note
			else:
				if order.type == 'sale':
					sale_terms = self.env['fischerbell.sale.terms.and.conditions'].search([('type','=','sale')], limit=1)
					order.terms_and_conditions = sale_terms.note
				elif order.type == 'loan':
					loan_terms = self.env['fischerbell.sale.terms.and.conditions'].search([('type','=','loan')], limit=1)
					order.terms_and_conditions = loan_terms.note
				elif order.type == 'exchange':
					exchange_terms = self.env['fischerbell.sale.terms.and.conditions'].search([('type','=','exchange')], limit=1)
					order.terms_and_conditions = exchange_terms.note
				elif order.type == 'training':
					training_terms = self.env['fischerbell.sale.terms.and.conditions'].search([('type','=','training')], limit=1)
					order.terms_and_conditions = training_terms.note
				else:
					replacement_terms = self.env['fischerbell.sale.terms.and.conditions'].search([('type','=','replacement')], limit=1)
					order.terms_and_conditions = replacement_terms.note


	def _prepare_invoice(self):
		invoice_vals = super()._prepare_invoice()
		invoice_vals['sale_id'] = self.id
		invoice_vals['invoice_instruction'] = self.invoice_instruction
		return invoice_vals

	def action_view_purchase_order(self):
		self.ensure_one()
		purchase_order_ids = self._get_purchase_orders().ids
		action = {
			'res_model': 'purchase.order',
			'type': 'ir.actions.act_window',
		}
		if len(purchase_order_ids) == 1:
			action.update({
				'view_mode': 'form',
				'res_id': purchase_order_ids[0],
			})
		else:
			action.update({
				'name': _("Purchase Order generated from %s", self.name),
				'domain': [('id', 'in', purchase_order_ids)],
				'view_mode': 'tree,form',
			})
		return action


	def _compute_billing_state(self):
		for order in self:
			order.billing_state = 'no_invoice'
			if order.invoice_status == 'invoiced':
				for inv in order.invoice_ids:
					if inv.payment_state in ['paid','in_payment']:
						order.billing_state = 'closed'
					else:
						order.billing_state = 'open'
			else:
				order.billing_state = 'open'

	def action_view_delivery(self):
		self.ensure_one()
		return {
			'name': 'Delivery',
			'type': 'ir.actions.act_window',
			'view_mode': 'tree,form,calendar',
			'res_model': 'stock.picking',
			'domain': [('id', 'in', self.mapped('picking_ids').ids)],
			'context': {'picking_id': self.mapped('picking_ids').ids}
		}


	@api.onchange('partner_id')
	def onchange_partner_invoice_id(self):
		relation_ids = []
		child_ids = []
		if self.partner_invoice_id:
			self.invoice_instruction = self.partner_invoice_id.invoice_instruction
			relation_ids = [x.id for x in self.partner_id.child_ids]
			# return {'domain':{'partner_invoice_id': [('id', 'in', relation_ids)],}}
		if self.partner_shipping_id:
			self.delivery_instruction = self.partner_shipping_id.delivery_instruction
			child_ids = [x.id for x in self.partner_id.child_ids]
			# return {'domain': {'partner_shipping_id': [('id', 'in', child_ids)]}}
		if self.partner_invoice_id and not self.partner_invoice_id.street and not self.partner_invoice_id.street2 and not self.partner_invoice_id.city and not self.partner_invoice_id.state_id and not self.partner_invoice_id.zip and not self.partner_invoice_id.country_id:
			self.check_partner_address = False
		else:
			self.check_partner_address = True
		if not self.partner_invoice_id:
			self.check_partner_address = False
		return {'domain': {'partner_shipping_id': [('id', 'in', child_ids),('type','=','delivery')],'partner_invoice_id': [('id', 'in', relation_ids),('type','=','invoice')]}}

	# ---------------------------------------------------------------------------------
	# ----------------- SEND MAIL TRIGGERS --------------------------------------------
	# ---------------------------------------------------------------------------------

	def send_mail_triggers_based_on_state(self):
		"""
			Send email based on the order's state
		"""
		sale_draft_trigger_templ = self.env.ref('fischerbell_custom.email_template_sale_draft_trigger')
		sale_sale_state_trigger_templ = self.env.ref('fischerbell_custom.email_template_sale_sale_state_trigger')
		if self.state == 'draft':
			sale_draft_trigger_templ.send_mail(res_id=self.id)
		elif self.state == 'sale':
			sale_sale_state_trigger_templ.send_mail(res_id=self.id)
		return True

	@api.model
	def create(self, vals):
		name = ''
		partner = False
		if vals.get('partner_invoice_id'):
			partner = self.env['res.partner'].search([('id','=',vals.get('partner_invoice_id'))],limit=1)

			if partner:
				name = name + "\n" + partner._display_address(without_company=True)
				vals['partner_invoice_address'] = name

		res = super().create(vals)
		# Send email to customer
		res.send_mail_triggers_based_on_state()
		return res

	@api.depends('picking_ids', 'picking_ids.state')
	def _compute_delivery_status(self):
		super(SaleOrder, self)._compute_delivery_status()
		sale_picking_pending_state_trigger_templ = self.env.ref('fischerbell_custom.email_template_sale_picking_pending_state_trigger')
		sale_picking_done_state_trigger_templ = self.env.ref('fischerbell_custom.email_template_sale_picking_done_state_trigger')
		for order in self:
			if order.delivery_status == 'pending':
				sale_picking_pending_state_trigger_templ.send_mail(res_id=order.id)
			elif order.delivery_status == 'full':
				sale_picking_done_state_trigger_templ.send_mail(res_id=order.id)

	def write(self, vals):
		name = ''
		partner = False
		if vals.get('partner_invoice_id'):
			partner = self.env['res.partner'].search([('id','=',vals.get('partner_invoice_id'))],limit=1)

			for order in self:
				if partner:
					name = name + "\n" + partner._display_address(without_company=True)
					order.partner_invoice_address = name
					order.check_partner_address = True
				if not order.partner_invoice_address:
					order.check_partner_address = False

		for order in self:
			if vals.get('state') == 'sale' and order.approval_state == 'no':
				vals['approval_state'] = 'waiting_approval'
				vals['state'] = 'waiting_approval'

			if vals.get('state') == 'cancel':
				vals['approval_state'] = 'reject'
				for mrp in order.mrp_production_ids:
					mrp.state = 'cancel'

			if vals.get('state') == 'draft':
				vals['approval_state'] = 'no'

			if vals.get('state') == 'sent':
				vals['email_to_customer'] = datetime.now()

			if vals.get('order_line'):
				order_line_vals = list(map(lambda y:list(y[-1].keys()),filter(lambda x:isinstance(x,list) and isinstance(x[-1],dict),vals.get('order_line'))))
				if any(field in ORDER_LINE_FIELDS for field in list(itertools.chain(*order_line_vals))):
					vals['revision_order_name'] = (order.name.split('-')[0] if not order.revision_order_name else order.revision_order_name.split('-')[0]) + '-R%s'%(int(order.revision_order_count + 1) if int(order.revision_order_count) == 0 else int(order.revision_order_count))
					vals['name'] = (order.name.split('-')[0] if not order.revision_order_name else order.revision_order_name.split('-')[0]) + '-R%s'%(int(order.revision_order_count + 1) if int(order.revision_order_count) == 0 else int(order.revision_order_count))
					vals['revision_order_count'] = order.revision_order_count + 1
					vals['is_order_revise'] = True

		res = super().write(vals)
		for order in self:
			if vals.get('tag_ids'):
				for pick in order.picking_ids:
					pick.tag_ids = vals['tag_ids']

		return res


	@api.depends('type','picking_ids', 'picking_ids.state')
	def _compute_loan_state(self):
		for order in self:
			order.loan_date = False
			order.loan_state = 'not_loan'
			if order.type == 'loan' and order.picking_ids:
				for pick in order.picking_ids:
					if pick.is_return_loan and pick.state != 'done' and pick.picking_type_code == 'incoming':
						order.loan_state = 'open'
					elif pick.is_return_loan and pick.state == 'done' and pick.picking_type_code == 'incoming':
						order.loan_state = 'closed'
						order.loan_date = fields.Date.today()
					else:
						order.loan_state = 'open'
			elif order.type == 'loan' and not order.picking_ids:
				order.loan_state = 'open'
			else:
				order.loan_state = 'not_loan'



	def create_loan_orders(self):
		for sale in self:
			sale_id = sale.create({
				'sale_id': sale.id,
				'partner_id': sale.partner_id.id,
				'partner_invoice_id': sale.partner_invoice_id.id,
				'partner_shipping_id': sale.partner_shipping_id.id,
				'pricelist_id': sale.pricelist_id.id,
				'type': 'loan',
				'state': 'draft',
			})

		return


	@api.depends('loan_ids')
	def _compute_loan_ids(self):
		for order in self:
			loan_ids = list(filter(lambda x: (x.type == 'loan'), order.loan_ids))
			order.loan_order_count = len(loan_ids)


	def action_view_loan_order(self):
		self.ensure_one()
		return {
			'type': 'ir.actions.act_window',
			'name': 'Loan Orders',
			'view_mode': 'tree,form',
			'res_model': 'sale.order',
			'domain': [('sale_id', '=', self.id),('type','=','loan')],
			'context': {'default_sale_id':self.id, 'default_type': 'loan', 'form_view_ref': 'sale.view_order_form', 'tree_view_ref':'sale.view_order_tree'},
			'tag': 'reload'
		}

	# def create_exchange_order(self):
	# 	for sale in self:
	# 		sale_id = sale.create({
	# 			'sale_id': sale.id,
	# 			'partner_id': sale.partner_id.id,
	# 			'partner_invoice_id': sale.partner_invoice_id.id,
	# 			'partner_shipping_id': sale.partner_shipping_id.id,
	# 			'pricelist_id': sale.pricelist_id.id,
	# 			'type': 'exchange',
	# 			'state': 'draft',
	# 		})
	#
	# 	return

	# @api.depends('exchange_order_ids')
	# def _compute_exchange_order_ids(self):
	# 	for order in self:
	# 		exchange = list(filter(lambda x: (x.type == 'exchange'), order.exchange_order_ids))
	# 		order.exchange_order_count = len(exchange)


	# def action_view_exchange_order(self, order=False):
	# 	self.ensure_one()
	#
	# 	return {
	# 		'type': 'ir.actions.act_window',
	# 		'name': 'Exchange Order',
	# 		'view_mode': 'tree,form',
	# 		'res_model': 'sale.order',
	# 		'domain': [('sale_id', '=', self.id),('type','=','exchange')],
	# 		'context': {'default_sale_id':self.id, 'default_type': 'exchange', 'form_view_ref': 'sale.view_order_form', 'tree_view_ref':'sale.view_order_tree'}
	# 	}


	# def create_replacement_orders(self):
	# 	for sale in self:
	# 		sale_id = sale.create({
	# 			'sale_id': sale.id,
	# 			'partner_id': sale.partner_id.id,
	# 			'partner_invoice_id': sale.partner_invoice_id.id,
	# 			'partner_shipping_id': sale.partner_shipping_id.id,
	# 			'pricelist_id': sale.pricelist_id.id,
	# 			'type': 'replacement',
	# 			'state': 'draft',
	# 		})
	#
	# 	return


	# @api.depends('replacement_order_ids')
	# def _compute_replacement_order_ids(self):
	# 	for order in self:
	# 		replacement = list(filter(lambda x: (x.type == 'replacement'), order.replacement_order_ids))
	# 		order.replacement_order_count = len(replacement)


	# def action_view_replacement_order(self, order=False):
	# 	self.ensure_one()
	#
	# 	return {
	# 		'type': 'ir.actions.act_window',
	# 		'name': 'Replacement Order',
	# 		'view_mode': 'tree,form',
	# 		'res_model': 'sale.order',
	# 		'domain': [('sale_id', '=', self.id),('type','=','replacement')],
	# 		'context': {'default_sale_id':self.id, 'default_type': 'replacement', 'form_view_ref': 'sale.view_order_form', 'tree_view_ref':'sale.view_order_tree'}
	# 	}

	def get_report_name(self):
		self.ensure_one()
		return '%s - %s %s'%(datetime.now().year,self.name or '',self.partner_id.parent_id.name or self.partner_id.name)

	def get_order_template_subject(self):
		self.ensure_one()
		if self.is_order_revise and self.user_id.id == self.env.user.id:
			return "This is a revised quotation %s."%(self.revision_order_name)
		else:
			return "%s %s (%s)"%(self.company_id.name,self.state in ('draft', 'sent') and (self._context.get('proforma') and 'Proforma' or 'Quotation') or 'Order',self.name or 'n/a')

	# Set first followup date in order cron.
	def cron_set_followup_date(self):
		for rec in self.search([
				('state', '=', 'draft'),  # Assuming 'draft' is the status of quotations
				('date_order', '<=', fields.Date.today() - timedelta(days=7)),
				('first_followup_date', '=', False)
			]):
			rec.first_followup_date = datetime.now()

	def cron_set_sec_followup_date(self):
		for rec in self.search([
				('state', '=', 'draft'),  # Assuming 'draft' is the status of quotations
				('first_followup_date', '!=', False),
				('first_followup_date', '<=', fields.Date.today() - timedelta(days=7))
			]):
			rec.sec_followup_date = datetime.now()

	def cron_reminder_customer_to_status(self):
		user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
		today = user_tz.localize(fields.Datetime.from_string(fields.Date.context_today(self))) - timedelta(days=7)
		date_start = today.astimezone(pytz.timezone('UTC'))
		date_stop = date_start + timedelta(days=1, seconds=-1)
		for rec in self.env['sale.order'].search([
									('state', '!=', 'sale'),
									('create_date', '>=', date_start),
									('create_date', '<=', date_stop),
				]):
			if rec:
				print("------rec",rec)
				display_message = """
										<p>We noticed that your order with reference number """ + rec.name + """ is still pending confirmation. 
										If you have any inquiries or concerns regarding this order, please feel free to reach out. 
										We are here to assist you and ensure a smooth process.</p>
										"""
				subject = (f""" Inquiry about Order  %s  Confirmation Status""" % rec.name)
				email_to = rec.partner_id.email
				mails = {
					'subject': subject,
					'email_from': self.env.user.email_formatted,
					'email_to': email_to,
					'body_html': display_message,
					'auto_delete': False,
				}
				mail = self.env['mail.mail'].create(mails)
				mail.send()
	def cron_reminder_processing_team_to_followup(self):
		user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
		today = user_tz.localize(fields.Datetime.from_string(fields.Date.context_today(self))) - timedelta(days=14)
		date_start = today.astimezone(pytz.timezone('UTC'))
		date_stop = date_start + timedelta(days=1, seconds=-1)
		for rec in self.env['sale.order'].search([
									('state', '!=', 'sale'),
									('create_date', '>=', date_start),
									('create_date', '<=', date_stop),
				]):
			if rec:
				print("------rec",rec)
				display_message = """
										<p>For this order """ + rec.name + """, since the customer has not responded, kindly proceed with a follow-up, meeting, or phone call to engage with the customer.</p>
										"""
				subject = (f""" Action Required for Quotation %s Customer Follow-Up Needed """ % rec.name)
				email_to = rec.user_id.email
				mails = {
					'subject': subject,
					'email_from': self.env.user.email_formatted,
					'email_to': email_to,
					'body_html': display_message,
					'auto_delete': False,
				}
				mail = self.env['mail.mail'].create(mails)
				mail.send()


class SaleOrderLine(models.Model):
	_inherit = "sale.order.line"

	product_code = fields.Char('Product Code', related="product_template_id.default_code")
	customer_id = fields.Many2one('res.partner', 'Customer', related="order_id.partner_id")
	customer_sku = fields.Char('Customer SKU')
	bp_code = fields.Char('BP Code')
	batch_number = fields.Char('Batch Number')
	use_bp_code = fields.Boolean('Use BP code',related="product_template_id.use_bp_code")
	use_product_batch_number = fields.Boolean('Use Product Batch Number', related="product_template_id.use_product_batch_number")
	lead_time_stock = fields.Char('Lead Time Stock', compute="_compute_lead_time_stock", store=True)
	terms_and_condition_ids = fields.Many2many('fischerbell.product.terms.and.conditions', string="Terms & Conditions", related="product_id.terms_and_condition_ids")
	last_invoice_date = fields.Datetime(string="Last Invoice Date",compute="_compute_get_last_invoice_date")
	last_invoice_price = fields.Float(string="Last Invoice Price",compute="_compute_get_last_invoice_date")
	last_price = fields.Float('Last Order Price', compute="_compute_last_order_price", store=True)
	picking_id = fields.Many2one('stock.picking', 'Picking')
	product_detail_sheet_url = fields.Char(related="product_id.product_detail_sheet_url")


	@api.depends('customer_id','product_id')
	def _compute_last_order_price(self):
		for price in self:
			last_price = self.search([('customer_id','=', price.customer_id.id),('product_id','=',price.product_id.id ),('state','=','sale')],limit=1)
			price.last_price = last_price.price_unit if last_price else 0

	def _compute_get_last_invoice_date(self):
		move_line_obj = self.env['account.move.line']
		for rec in self:
			invoice_ids = move_line_obj.search([('product_id','=',rec.product_id.id),('move_id.state','=','posted')]).mapped('move_id')
			rec.last_invoice_date = False
			rec.last_invoice_price = False
			if invoice_ids:
				last_invoice_date = min(invoice_ids.mapped('create_date'))
				last_invoice_id = self.env['account.move'].search([('create_date','=',last_invoice_date)])
				rec.last_invoice_date = last_invoice_id.create_date
				rec.last_invoice_price = move_line_obj.search([('product_id','=',rec.product_id.id),('move_id','=',last_invoice_id.id)],limit=1).price_unit

	@api.depends('product_template_id.virtual_available')
	def _compute_lead_time_stock(self):
		self.lead_time_stock = ''
		for line in self:
			if line.product_template_id.virtual_available > 0:
				line.lead_time_stock = 'Ex-Stock'
			else:
				line.lead_time_stock = 'Indent'


	@api.onchange('product_template_id')
	def onchange_sale_customer_sku(self):
		if self.customer_id and self.product_template_id and self.product_template_id.use_customer_sku:
			customer_sku = ''
			for line in self.product_template_id.customer_sku_ids:
				if line.customer_id == self.customer_id and line.customer_sku:
					customer_sku = line.customer_sku
			if customer_sku:
				self.customer_sku = customer_sku
			else:
				self.customer_sku = ''
		else:
			self.customer_sku = ''

		if self.product_template_id and self.product_template_id.use_bp_code and self.product_template_id.bp_code:
			self.bp_code = self.product_template_id.bp_code
		else:
			self.bp_code = ''


	@api.onchange('price_unit')
	def onchange_price_unit(self):
		if self.price_unit:
			if self.price_unit > self.product_template_id.max_price:
				raise ValidationError("Sales price is greater than maximal price")
			if  self.price_unit < self.product_template_id.min_price:
				raise ValidationError("Sales price is less than minimal price")
