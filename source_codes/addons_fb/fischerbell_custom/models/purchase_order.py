# -*- coding: utf-8 -*-

import itertools
import calendar

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date
from odoo.tools.float_utils import float_round

PURCHASE_LINE_FIELDS = ['product_qty','price_unit','price_subtotal','taxes_id']

class PurchaseOrder(models.Model):
	_inherit = "purchase.order"

	internal_note = fields.Text('Notes')
	supplier_code = fields.Char('Vendor Code', related="partner_id.supplier_code")
	amount_undiscounted = fields.Float('Amount Before Discount', compute='_compute_purchase_amount_undiscounted', digits=0)
	sale_id = fields.Many2one('sale.order', 'Sale')
	journal_id = fields.Many2one('account.journal', 'Billing Mode')
	user = fields.Many2one('res.users', default=lambda self: self.env.user)
	today = fields.Datetime('Date and Time', default=datetime.now())
	purchase_team_id = fields.Many2one('res.users', default=lambda self: self.env.user)
	len_note = fields.Char('Length Internal Notee', compute="_compute_purchase_internal_note", store=True)
	partner_note = fields.Text('Note')
	is_default_terms = fields.Boolean('Is Default Terms')
	po_comments = fields.Char(string="Comments")
	request_delivery_date = fields.Datetime("Request Delivery Date")
	estimated_delivery_date = fields.Datetime("Estimated Delivery Date")
	revision_purchase_count = fields.Float(sting="Revision Purchase Count",default=1.0)
	revision_purchase_name = fields.Char(sting="Revision Purchase Name")
	is_purchase_revise = fields.Boolean(default=False)
	artwork_attachment_ids = fields.Many2many('ir.attachment', string="ArtWork")
	mail_sended = fields.Boolean(default=False)
	state = fields.Selection(
		selection_add=[
			("approved", "Approved"),
		]
	)

	def sc_approved(self):
		for rec in self:
			rec.state = "approved"

	def action_is_default_terms_purchase(self):
		purchase = self.env['stock.picking'].search([('is_default_terms','=',True)], limit=1)
		if purchase:
			purchase.is_default_terms = False
		else:
			for po in self:
				po.is_default_terms = True
		for po in self:
			po.is_default_terms = True

	@api.model
	def create(self, vals):
		res = super(PurchaseOrder, self).create(vals)
		default_terms = self.env['purchase.order'].search([('is_default_terms','=',True)], limit=1).notes
		if default_terms:
			vals['notes'] = default_terms
		return res
	
	def write(self,vals):
		for purchase in self:
			if vals.get('order_line'):
				order_line_vals = list(map(lambda y:list(y[-1].keys()),filter(lambda x:isinstance(x,list) and isinstance(x[-1],dict),vals.get('order_line'))))
				if any(field in PURCHASE_LINE_FIELDS for field in list(itertools.chain(*order_line_vals))):
					vals['revision_purchase_name'] = (purchase.name.split('-')[0] if not purchase.revision_purchase_name else purchase.revision_purchase_name.split('-')[0]) + '-R%s'%(int(purchase.revision_purchase_count + 1) if int(purchase.revision_purchase_count) == 0 else int(purchase.revision_purchase_count))
					vals['name'] = (purchase.name.split('-')[0] if not purchase.revision_purchase_name else purchase.revision_purchase_name.split('-')[0]) + '-R%s'%(int(purchase.revision_purchase_count + 1) if int(purchase.revision_purchase_count) == 0 else int(purchase.revision_purchase_count))
					vals['revision_purchase_count'] = purchase.revision_purchase_count + 1
					vals['is_purchase_revise'] = True
		return super(PurchaseOrder,self).write(vals)

	@api.depends('partner_note')
	def _compute_purchase_internal_note(self):
		self.len_note = False
		for inv in self:
			if inv.partner_note:
				inv.len_note = len(inv.partner_note)
			else:
				inv.len_note = False

	def _compute_purchase_amount_undiscounted(self):
		for order in self:
			total = 0.0
			for line in order.order_line:
				total += line.price_subtotal + line.price_unit * ((line.discount or 0.0) / 100.0) * line.product_uom_qty  # why is there a discount in a field named amount_undiscounted ??
			order.amount_undiscounted = total

	def _prepare_invoice(self):
		"""Prepare the dict of values to create the new invoice for a purchase order.
		"""
		self.ensure_one()
		move_type = self._context.get('default_move_type', 'in_invoice')

		partner_invoice = self.env['res.partner'].browse(self.partner_id.address_get(['invoice'])['invoice'])
		partner_bank_id = self.partner_id.commercial_partner_id.bank_ids.filtered_domain(['|', ('company_id', '=', False), ('company_id', '=', self.company_id.id)])[:1]


		invoice_vals = {
			'ref': self.partner_ref or '',
			'move_type': move_type,
			'narration': self.notes,
			'currency_id': self.currency_id.id,
			'invoice_user_id': self.user_id and self.user_id.id or self.env.user.id,
			'partner_id': partner_invoice.id,
			'fiscal_position_id': (self.fiscal_position_id or self.fiscal_position_id._get_fiscal_position(partner_invoice)).id,
			'payment_reference': self.partner_ref or '',
			'partner_bank_id': partner_bank_id.id,
			'invoice_origin': self.name,
			'invoice_payment_term_id': self.payment_term_id.id,
			'invoice_line_ids': [],
			'company_id': self.company_id.id,
			'purchase_order_id': self.id
		}
		return invoice_vals


	@api.onchange('partner_id')
	def onchange_partner_to_get_purchasenote(self):
		for order in self:
			if order.partner_id:
				config_note = self.env['fischerbell.configuration.note'].search([
			        ('type', '=', 'purchase'),
			        ('partner_ids', 'in', [order.partner_id.id])  # Use a list to compare with a Many2many field
			    ], limit=1)
				order.partner_note = config_note.note


	def button_confirm(self):
		# if self.request_delivery_date and self.estimated_delivery_date and self.mail_sended:
		if self.mail_sended:
			res = super().button_confirm()
			for order in self:
				if order.picking_ids:
					for pick in order.picking_ids:
						pick.user = self.env.user.id
			return res
		else:
			if not self.mail_sended:
				raise ValidationError("Please Send Email First")

	def _prepare_picking(self):
		res = super(PurchaseOrder, self)._prepare_picking()
		res.update({"artwork_attachment_ids": [(6, 0, self.artwork_attachment_ids.ids)]})
		return res

	def check_planned_date(self, order_date_planned):
		if order_date_planned:
			partner_ids = self.partner_id
			for partner_id in partner_ids:
				if partner_id.no_delivery_days_selection == 'days':
					if eval(partner_id.no_delivery_days) == order_date_planned.weekday():
						raise UserError('The customer %s is not available at this day %s, please change it as per the customers availability' % (partner_id.name,calendar.day_name[eval(partner_id.no_delivery_days)]))
				elif partner_id.no_delivery_days_selection == 'date':
					if partner_id.delivery_restriction_start_date <= order_date_planned.date() <= partner_id.delivery_restriction_end_date:
						raise UserError('The customer %s is not available at this date %s, please change it as per the customers availability' % (partner_id.name,order_date_planned))
	

	@api.depends('order_line.date_planned')
	def _compute_date_planned(self):
		""" date_planned = the earliest date_planned across all order lines. """
		for order in self:
			dates_list = order.order_line.filtered(lambda x: not x.display_type and x.date_planned).mapped('date_planned')
			if dates_list:
				order.date_planned = min(dates_list)
			else:
				order.date_planned = False
			self.check_planned_date(order.date_planned)

class PurchaseOrderLine(models.Model):
	_inherit = "purchase.order.line"

	customer_id = fields.Many2one('res.partner', 'Customer Name')
	batch_number = fields.Char('Batch Number', related="customer_id.batch_number")
	lot_id = fields.Many2one('stock.lot', 'Serial Number')
	product_tmpl_id = fields.Many2one('product.template')
	discount = fields.Float(string='Discount (%)', digits='Discount', default=0.0)
	product_template_id = fields.Many2one('product.template', 'Product Template', related="product_id.product_tmpl_id")
	customer_sku = fields.Char('Customer SKU')
	sale_id = fields.Many2one('sale.order', related="sale_line_id.order_id")
	manufacture_lot_id = fields.Many2one('fischerbell.manufacture.lot', 'Manufacture No')
	comments = fields.Char()

	@api.onchange('customer_id')
	def onchange_purchase_customer_sku(self):
		if self.customer_id and self.product_id.product_tmpl_id and self.product_id.product_tmpl_id.use_customer_sku:
			customer_sku = ''
			for line in self.product_id.product_tmpl_id.customer_sku_ids:
				if line.customer_id == self.customer_id and line.customer_sku:
					customer_sku = line.customer_sku
			if customer_sku:
				self.customer_sku = customer_sku
			else:
				self.customer_sku = ''
		else:
			self.customer_sku = ''

	def _get_product_purchase_description(self, product_lang):
		self.ensure_one()
		size = ''
		for product in product_lang.product_variant_ids:
			if product_lang == product:
				for line in product.product_template_variant_value_ids:
					size += line.display_name
		name = product_lang.name
		if product_lang.description_purchase and size:
			name += ' ' + size + '\n' + product_lang.description_purchase
		elif product_lang.description_purchase:
			name += '\n' + product_lang.description_purchase
		elif size:
			name += ' ' + size
		else:
			pass
		return name


	def _prepare_account_move_line(self, move=False):
		res = super()._prepare_account_move_line()
		sale_ids = False
		picking_ids = False
		move_ids = False
		context = self._context
		list_so = []
		invoice_vals = False
		for line in self:
			if context.get('create_bill') == True:
				list_so.append(line.sale_line_id.order_id.id)
				if list_so:
					sale_ids = self.env['sale.order'].search([('id', 'in', list_so)])
					picking_ids = self.env['stock.picking'].search([('sale_id', 'in', sale_ids.ids),('picking_type_code','=','outgoing'),('state','!=','cancel')])
					move_ids = self.env['account.move'].search([('move_type','=','out_invoice'),('sale_id','in',sale_ids.ids)])

		res.update({'sale_ids': sale_ids,'move_ids': move_ids, 'picking_ids': picking_ids})
		return res
