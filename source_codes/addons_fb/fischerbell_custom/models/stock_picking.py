# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api,fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tests import Form
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from PyPDF2 import PdfFileReader, PdfFileWriter
from io import BytesIO
from datetime import timedelta

class Picking(models.Model):
	_inherit = "stock.picking"

	def _get_stock_status_from_so(self):
		for rec in self:
			if rec.sale_id:
				return rec.sale_id.no_enough_stock
			else:
				True
	is_return_loan = fields.Boolean("Is Return Loan", default=False)
	partner_address = fields.Char('Address')
	partner_type =  fields.Selection(
		[('contact', 'Contact'),
		 ('invoice', 'Invoice Address'),
		 ('delivery', 'Delivery Address'),
		 ('private', 'Private Address'),
		 ('other', 'Other Address'),
		 ('followup', 'Pickup Address')
		], string='Partner Type', related="partner_id.type")
	return_picking_type_id = fields.Many2one('stock.picking.type',string="Operation Type for Returns", related="picking_type_id.return_picking_type_id")
	pick_id = fields.Many2one('stock.picking')
	is_purchase_return = fields.Boolean('Is Purchase Return', default=False)
	is_printed = fields.Boolean('Is Printed', default=False)
	print_date = fields.Datetime('Print Date')
	operation_id = fields.Many2one('mrp.production', 'Manufacture Order')
	user = fields.Many2one('res.users', default=lambda self: self.env.user)
	today = fields.Datetime('Date and Time', default=datetime.now())
	len_note = fields.Char('Length Internal Note', compute="_compute_picking_internal_note", store=True)
	partner_note = fields.Text('Note')
	delivery_type = fields.Selection([
		('self_collection', 'Self Collection'),
		('in_house_driver', 'Delivery by In-house Driver'),
		('third_party_logistics','Delivery by Third-party Logistics')
	], default='self_collection', related="sale_id.delivery_type")
	tag_ids = fields.Many2many('crm.tag', 'picking_crm_tag_rel', 'picking_id','crm_tag_id', string="Tags")
	route_id = fields.Many2one('fischerbell.delivery.route', 'Delivery Route', related="sale_id.route_id")
	po_type = fields.Selection([
		('open', 'Open'),
		('closed', 'Closed'),
		('cancel','Cancel')
	], string='Type Of Purchase', compute="_compute_po_type", store=True)
	terms_and_conditions = fields.Text('Terms and Conditions')
	is_default_terms = fields.Boolean('Is Default Terms')
	order_lines = fields.One2many('service.type.product.line', 'picking_id', string="Order Line")
	# total_qty_line = fields.Float('Total', compute="_compute_total_qty", store=True)
	enough_stock = fields.Boolean(default=_get_stock_status_from_so)
	artwork_attachment_ids = fields.Many2many('ir.attachment', string="ArtWork")
	next_delivery_date = fields.Datetime('Next Delivery Date')
	delivery_instruction = fields.Html(string="Delivery Instruction")
	invoice_instruction = fields.Html(string="Invoice Instruction")
	state = fields.Selection(selection_add=[('cancel_approval','Cancel Approval')])
	cancel_request_by = fields.Many2one("res.users",string="Cancel Request By")
	cancellation_reason = fields.Text(string="Cancellation Reason")
	past_state = fields.Char("Past State")
	is_exceed_picking = fields.Boolean()
	assigned_date = fields.Datetime(string="Assigned Date", readonly=True, copy=False)
	

	def action_cancel(self):
		for picking in self:
			if picking.picking_type_code == 'incoming' :
				return {
					'type': 'ir.actions.act_window',
					'name': 'Cancel Transfer',
					'res_model': 'stock.picking.cancellation.wizard',
					'view_mode': 'form',
					'target': 'new',
					'context': {
						'default_stock_picking_id': picking.id,
					},
				}
			else :
				return super(Picking, self).action_cancel()

	def cancellation_request_approved(self) :
		for picking in self : 
			picking.write({'state': 'cancel'})
			requester = picking.cancel_request_by.partner_id
			if requester:
				picking.message_post(
					body=f"Your cancellation request for Transfer {picking.name} has been approved.",
					partner_ids=[requester.id]
				)

	def cancellation_request_rejected(self) :
		for picking in self:
			if picking.past_state :
				picking.write({'state': picking.past_state})
			
			# Notify requester about rejection
			requester = picking.cancel_request_by.partner_id
			if requester:
				picking.message_post(
					body=f"Your cancellation request for Transfer {picking.name} has been rejected.",
					partner_ids=[requester.id]
				)

	def action_update_schedule_date(self):
		for obj in self:
			if obj.state in ('draft', 'cancel', 'done'):
				continue
			if obj.backorder_id and obj.scheduled_date:
				for line in obj.move_ids_without_package:
					if line.purchase_line_id:
						line.purchase_line_id.estimated_delivery_date = obj.scheduled_date


	@api.depends('move_ids.state', 'move_ids.date', 'move_type')
	def _compute_scheduled_date(self):
		for picking in self:
			moves_dates = picking.move_ids.filtered(lambda move: move.state not in ('done', 'cancel')).mapped(
				'date')
			if picking.purchase_id:
				if picking.purchase_id and picking.purchase_id.estimated_delivery_date:
					picking.scheduled_date = picking.purchase_id.estimated_delivery_date
				else:
					picking.scheduled_date = fields.Datetime.now()
			elif picking.sale_id:
				# picking.scheduled_date =  picking.sale_id.scheduled_delivery_date or fields.Datetime.now()
				if picking.purchase_id and picking.purchase_id.estimated_delivery_date:
					picking.scheduled_date = picking.purchase_id.estimated_delivery_date or fields.Datetime.now()
				else:
					picking.scheduled_date = min(moves_dates, default=picking.scheduled_date or fields.Datetime.now())
			else:
				if picking.move_type == 'direct':
					picking.scheduled_date = min(moves_dates, default=picking.scheduled_date or fields.Datetime.now())
				else:
					picking.scheduled_date = max(moves_dates, default=picking.scheduled_date or fields.Datetime.now())


	def action_is_default_terms(self):
		picking = self.env['stock.picking'].search([('is_default_terms','=',True)], limit=1)
		if picking:
			picking.is_default_terms = False
		else:
			for pick in self:
				pick.is_default_terms = True

		for pick in self:
			pick.is_default_terms = True



	@api.depends('state')
	def _compute_po_type(self):
		for picking in self:
			if picking.state == 'done':
				picking.po_type = 'closed'
			elif picking.state == 'cancel':
				picking.po_type = 'cancel'
			else:
				picking.po_type = 'open'


	@api.onchange('tag_ids')
	def onchange_picking_tag_ids(self):
		if self.tag_ids:
			self.sale_id.tag_ids = self.tag_ids


	@api.depends('partner_note')
	def _compute_picking_internal_note(self):
		self.len_note = False
		for inv in self:
			if inv.partner_note:
				inv.len_note = len(inv.partner_note)
			else:
				inv.len_note = False


	def generate_report(self, move):
		purchase_order_line = self.env['purchase.order.line'].search([('product_id', '=', move.product_id.id), ('manufacture_lot_id', '!=', False)], order='id asc')
		qty = move.product_uom_qty
		data_lot = []
		count = 0
		
		for rec in purchase_order_line:
			if qty > 0:
				if rec.product_qty >= qty:
					data_lot.append(rec.manufacture_lot_id.name)
					return data_lot

				else:
					data_lot.append(rec.manufacture_lot_id.name)
					qty -= rec.product_qty
			else:
				return data_lot
	
	# def check_product(self):
	# 	product = []
	# 	for rec in self.move_line_ids_without_package.mapped('product_id'):
	# 		product.append(rec)
	# 		return product
	
	# def generate_total_qty(self):
	# 	product_list = self.check_product()
	# 	total_qty = 0
	# 	total_option = []
	# 	for line in product_list:
	# 		for order in self.move_line_ids_without_package:
	# 			if order.product_id.id == line.id:
	# 				total_qty += order.qty_done

	# 		total_option.append({
	#             'product_id': line,
	# 			'default_code':line,
	#             'qty_done' : total_qty,
	# 			'product_uom_id': line,
				
	#         })
	# 		total_qty = 0
	# 	return total_option
	
	def generate_total_qty(self):
		total_option = [] 

		for product in self.move_line_ids_without_package.mapped('product_id'):
			total_qty = 0

			for order in self.move_line_ids_without_package.filtered(lambda x: x.product_id == product):
				total_qty += order.qty_done

			total_option.append({
				'product_id': product,
				'qty_done' : total_qty,
				'default_code':product,
				'product_uom_id': product,
			})

		return total_option

	# @api.depends('move_line_ids_without_package')
	# def _compute_total_qty(self):
	# 	for line in self.move_line_ids_without_package:
	# 		print(line, '========================line')
	# 		move_lines = []
	# 		product_quantity = {}
			
	# 		for move in line:
	# 			product_name = move.product_id.name
	# 			quantity = move.qty_done
	# 			print(product_name, '===============================name')
	# 			print(quantity, '======================================qty')
				
	# 			if product_name in product_quantity:
	# 				product_quantity[product_name] += quantity
	# 			else:
	# 				product_quantity[product_name] = quantity
					
	# 		for product_name, quantity in product_quantity.items():
	# 			move_lines.append({
	#                 'product_name': product_name,
	#                 'total_quantity': quantity,
	#             })
	# 		print(move_lines, 'moveeeeeeeeeeeeeeeeeeeeeeeeeeeeee==================')

	
	def print_report(self):
		action_report_delivery_order = self.env.ref('fischerbell_custom.action_report_delivery_order').report_action(self)
		action_report_delivery_order_rx_frame = self.env.ref('fischerbell_custom.action_report_delivery_order_rx_frame').report_action(self)
		context = action_report_delivery_order.get('context') or {}

		# action_report_delivery_order['data'] = context.get('active_ids')
		action_report_delivery_order['docs'] = self.env['stock.picking'].browse(context.get('active_ids'))
		action_report_delivery_order_rx_frame['docs'] = self.env['stock.picking'].browse(context.get('active_ids'))

		self.print_another_report(action_report_delivery_order_rx_frame)
		# pdf_a = PdfFileReader(BytesIO(action_report_delivery_order['pdf']))
		# pdf_b = PdfFileReader(BytesIO(action_report_delivery_order_rx_frame['pdf']))
		# with open('/report_a.pdf', 'wb') as f_a:
		# 	pdf_a.write(f_a)
		# with open('/report_b.pdf', 'wb') as f_b:
		# 	pdf_b.write(f_b)
		
		return action_report_delivery_order
	
	def print_another_report(self,action_report):
		print('second_functionsecond_functionsecond_functionsecond_function',action_report )
		return action_report



	def _compute_partner_address(self):
		name = ''
		self.partner_address = ''
		for pick in self:
			if pick.partner_id.type == 'followup':
				name = name + "\n" + pick.partner_id._display_address(without_company=True)
				pick.partner_address = name
			else:
				pick.partner_address = ''

	def _action_generate_backorder_wizard(self, show_transfers=False):
		if self.picking_type_code == 'incoming' and not self.env.user.has_group(
				'fischerbell_custom.group_purchase_user_approval'):
			raise UserError(
				'You do not have rights to create a Back order. Please contact your Purchase manager.')
		elif self.picking_type_code == 'outgoing' and not self.env.user.has_group(
				'fischerbell_custom.group_sale_user_approval'):
			raise UserError(
				'You do not have rights to create a Back order. Please contact your sale manager.')
		else:
			view = self.env.ref('stock.view_backorder_confirmation')
			return {
				'name': _('Create Backorder?'),
				'type': 'ir.actions.act_window',
				'view_mode': 'form',
				'res_model': 'stock.backorder.confirmation',
				'views': [(view.id, 'form')],
				'view_id': view.id,
				'target': 'new',
				'context': dict(self.env.context, default_show_transfers=show_transfers,
								default_pick_ids=[(4, p.id) for p in self]),
			}
	def _send_grn_notification(self):
		"""Send email notification when GRN is validated."""
		# Fetch emails from res.config.settings
		email_string = self.env['ir.config_parameter'].sudo().get_param(
			'account.vendor_bill_notification_emails', default=''
		)
		email_list = [email.strip() for email in email_string.split(',') if email.strip()]

		if not email_list:
			return  # No emails configured, skip sending

		# Load the email template
		template = self.env.ref('fischerbell_custom.email_template_grn_notification', raise_if_not_found=False)
		if not template:
			raise ValidationError(_("Email template for GRN notification is missing."))
		email_values = {}
		for picking in self:
			if picking.picking_type_id.code == 'incoming':  # Ensure it's an incoming shipment
				email_values['email_to'] = ",".join(email_list)
				template.send_mail(picking.id, force_send=True, email_values=email_values)

	def button_validate(self):
		for picking in self:
			if picking.picking_type_code == 'outgoing' and len(picking.upload_images) == 0:
				raise ValidationError("Please Upload image after Validate Order!")
			if picking.picking_type_id.code == 'outgoing':
				template = self.env.ref('fischerbell_custom.email_template_delivery_confirmation', raise_if_not_found=False)
				if template and picking.partner_id.email:
					attachment_ids = [(4, attachment.id) for attachment in picking.upload_images]

					template.send_mail(picking.id, force_send=True,
						email_values = {
                			'attachment_ids': attachment_ids
						}
					)
			if not picking.enough_stock and picking.sale_id.delivery_option != 'partial_delivery':
								no_stock_line_ids = any(line.product_uom_qty > line.product_template_id.qty_available for line in picking.sale_id.order_line)
								if no_stock_line_ids:
										raise UserError('Product stock is not enough as demand. Customers wants wait till all stocks be ready for shipment.')
			#if picking.picking_type_code == 'internal:
				#raise ValidationError("Sorry you cannot validate, as this transfer is not yet check.")
			if picking.picking_type_code == 'incoming':
				picking._send_grn_notification()
				for move_line in picking.move_ids_without_package:
					qty = int(move_line.product_uom_qty)
					if move_line.quantity_done > move_line.product_uom_qty:
						raise ValidationError("Sorry, you cannot input the quantity more than "+str(qty))
					else:
						pass

			for operation in picking.move_line_ids_without_package:
				if operation.reserved_uom_qty <= 0 and picking.picking_type_code != 'incoming':
					raise ValidationError("Sorry, you cannot validate when the quantity is not reserved")


		res = super().button_validate()
		stock_picking = False
		for pick in self:
			if pick.picking_type_code == 'outgoing' and pick.state == 'done' and pick.sale_id.type == 'loan':
				context = self._context.get('loan_orders')
				stock_return_picking_form = Form(self.env['stock.return.picking'].with_context(active_ids=pick.ids, active_id=pick.ids[0],active_model='stock.picking', loan_orders=True))
				stock_return_picking = stock_return_picking_form.save()
				stock_return_picking_action = stock_return_picking.create_returns()
			else:
				pass

			stock_picking = self.env['stock.picking'].search([('sale_id','=',pick.sale_id.id),('picking_type_code','=','incoming'),('is_return_loan','=',True),('sale_id.type','=','loan')])


		if stock_picking:
			for pick_return in stock_picking:
				weeks = float(self.env['ir.config_parameter'].sudo().get_param('fischerbell_custom.return_time'))
				deadline = datetime.today() + relativedelta(weeks=weeks)
				pick_return.activity_schedule(summary='Reminder Collect Loan Item', date_deadline=deadline, user_id=self.env.user.id,  activity_type_id=self._default_activity_type().id)

				
				channel_id = self.env['mail.channel'].search([('is_sales_loan_management', '=', True)], limit=1)

				if channel_id:
					for partner in channel_id.channel_member_ids:
						user = self.env['res.users'].search([('partner_id', '=', partner.partner_id.id)])

						if user:
							pick_return.activity_schedule(summary='Reminder Collect Loan Item', date_deadline=deadline, user_id=user.id,  activity_type_id=self._default_activity_type().id)

		return res

	def _action_done(self):
		res = super()._action_done()
		for record in self : 
			if record.purchase_id and record.state == 'done' : 
				record.purchase_id.action_create_invoice() 
				record.purchase_id.button_done()
				for move_id in record.move_ids_without_package:
					if move_id.lot_ids.ids:
						lot_ids = self.env['stock.lot'].search([('id', 'in', move_id.lot_ids.ids)])
						lot_ids.write({'is_from_po': True})
			if record.ticket_id and record.ticket_id.service_type == 'outsource_service' and record.state == 'done':
				for move_id in record.move_ids_without_package:
					if move_id.lot_ids.ids:
						lot_ids = self.env['stock.lot'].search([('id', 'in', move_id.lot_ids.ids)])
						lot_ids.write({'is_from_service': True})

		return res


	def send_reminder_loan_item(self):
		picking = self.env['stock.picking'].search([('is_return_loan','=',True),('picking_type_code','=','incoming'),('state','!=','done')])
		for pick in picking:
			if pick.activity_ids:
				deadline = pick.activity_date_deadline
				today = fields.Date.today()
				if today > deadline:
					users = False
					channel_id = self.env['mail.channel'].search([('is_sales_loan_management', '=', True)], limit=1)
					if channel_id:
						for partner in channel_id.channel_member_ids:
							users = self.env['res.users'].search([('partner_id', '=', partner.partner_id.id)])

					email_to = ''
					if users:
						for user in users:
							email_to += user.partner_id.email


					if email_to:
						display_message="""
						<p><b>Reminder Collect Loan Item</b></p>
						<p>Return Orders : """+pick.name+"""
						"""
						subject = (f""" Reminder Collect Loan Item %s"""%pick.name)

						mails = {
							'subject': subject,
							'email_from': 'thankyou@lush-lush.com',
							'email_to': email_to,
							'reply_to': 'noreply-mail.com',
							'body_html': display_message,
							'auto_delete': False,
						}

						mail = self.env['mail.mail'].create(mails)
						mail.send()

						pick.message_post(
							subject="Reminder Collect Loan Item",
							body=display_message,
							partner_ids=pick.user_id.partner_id.ids
						)
					
	@api.model
	def create(self, vals):
		default_terms = self.env['stock.picking'].search([('is_default_terms','=',True)], limit=1).terms_and_conditions
		if default_terms:
			vals['terms_and_conditions'] = default_terms
		
		sale_id = None
		# if vals.get('origin'):
		# 	sale_id = self.env['sale.order'].search([('name', '=', vals.get('origin'))])
		# 	mrp = self.env['mrp.production'].search([('name','=',vals.get('origin'))], limit=1)

		# 	if mrp:
		# 		vals['operation_id'] = mrp.id

		if vals.get('picking_type_id'):
			picking_type = self.env['stock.picking.type'].search([('id','=',vals.get('picking_type_id')),('sequence_code','=','PICK'),('code','=','internal')])
			if sale_id and sale_id.partner_id and sale_id.partner_id.child_ids and vals.get('partner_id') and vals['picking_type_id'] == picking_type.id:
				for child in sale_id.partner_id.child_ids:
					if child.type == 'followup':
						vals['partner_id'] = child.id

			if sale_id:
				vals['tag_ids'] = sale_id.tag_ids.ids

		if vals.get('partner_id'):
			partner_id = self.env['res.partner'].search([('id','=',vals.get('partner_id'))], limit=1)
			if partner_id.parent_id:
				config_note = self.env['fischerbell.configuration.note'].search([
					('type', '=', 'picking'),
					('partner_ids', 'in', [partner_id.parent_id.id])  # Use a list to compare with a Many2many field
				], limit=1)
				vals['partner_note'] = config_note.note
			else:
				config_note = self.env['fischerbell.configuration.note'].search([
					('type', '=', 'picking'),
					('partner_ids', 'in', [partner_id.id])  # Use a list to compare with a Many2many field
				], limit=1)
				vals['partner_note'] = config_note.note

		res = super(Picking, self).create(vals)
		if vals.get('next_delivery_date') and res.purchase_id:
			res.purchase_id.next_delivery_date = vals.get('next_delivery_date')
		pick_order = self.env['stock.picking'].search([('picking_type_id.sequence_code','=','PICK'),('origin','=',res.origin)], limit=1)
		if res.picking_type_id.sequence_code == 'OUT':
			res.pick_id = pick_order

		date = fields.Date.today()
		pickings = False
		if vals.get('origin'):
			pickings = self.env['stock.picking'].search([('origin','=',vals.get('origin'))])

		if pickings:
			for pick in pickings:
				if pick.picking_type_code == 'outgoing' and sale_id:
					user = pick.sale_id.user_id
					salesperson_email = f"{sale_id.user_id.login}"
					res.activity_schedule(summary='To Print DO', date_deadline=date, user_id=user.id,  activity_type_id=self._default_activity_type().id)
					subject = (f""" Alert to print DO """)
					display_message="""
						<p>Hi, """+sale_id.user_id.name+""". Your """+sale_id.name+""" is ready to delivery. Please print delivery order """+pick.name+""".
						"""
					mails = {
						'subject': subject,
						'email_from': 'noreply-mail',
						'email_to': salesperson_email,
						'reply_to': 'noreply-mail.com',
						'body_html': display_message,
						'auto_delete': False,
					}
					mail = self.env['mail.mail'].create(mails)
					mail.send()

					pick.message_post(
						subject="Alert to print DO",
						body=display_message,
						partner_ids=pick.sale_id.user_id.partner_id.ids
					)
				else:
					pass
		return res

	def write(self, vals):
		if vals.get('partner_id'):
			partner_id = self.env['res.partner'].search([('id','=',vals.get('partner_id'))], limit=1)
			if partner_id.parent_id:
				config_note = self.env['fischerbell.configuration.note'].search([
					('type', '=', 'picking'),
					('partner_ids', 'in', [partner_id.parent_id.id])  # Use a list to compare with a Many2many field
				], limit=1)
				vals['partner_note'] = config_note.note
			else:
				config_note = self.env['fischerbell.configuration.note'].search([
					('type', '=', 'picking'),
					('partner_ids', 'in', [partner_id.id])  # Use a list to compare with a Many2many field
				], limit=1)
				vals['partner_note'] = config_note.note
		res = super(Picking, self).write(vals)
		if vals.get('next_delivery_date') and self.purchase_id:
			self.purchase_id.next_delivery_date = vals.get('next_delivery_date')
		for picking in self:
			picking.action_update_schedule_date()
			if picking.state == 'done' and picking.sale_id and picking.picking_type_code == 'outgoing' and not picking.sale_id.invoice_ids and picking.sale_id.type != 'loan':
				picking.sale_id._create_invoices()

			if picking.activity_ids and picking.is_printed and picking.print_date != False:
				for activity in picking.activity_ids:
					activity.action_done()

			if picking.is_return_loan and picking.state == 'cancel':
				for activity in picking.activity_ids:
					activity.action_done()
			# for obj in self:
			# 	obj.action_update_schedule_date()

		return res

	def send_email_to_customer(self):
		backorders = self.search([('backorder_id', '!=', False)], order='scheduled_date')
		sale_order_obj = self.env['sale.order']
		sale_orders = []
		for record in backorders:
			sale_order = sale_order_obj.search([('name', '=', record.origin)])
			for product_line in record.move_ids_without_package:
				if product_line.product_id:
					if product_line.product_uom_qty <= product_line.product_id.qty_available:
						if sale_order.partner_id.email not in sale_orders and sale_order.partner_id.email:
							sale_orders.append(sale_order.id)

		for order in sale_orders:
			sale_order_ref = sale_order_obj.search([('id', '=', order)])
			template = self.env.ref('fischerbell_custom.email_template_to_customer')
			email_values = {'email_to': sale_order_ref.partner_id.email}
			template.sudo().send_mail(sale_order_ref.id, email_values=email_values)


	def action_update_quantity(self):
		line_list = []
		for move_line in self.move_ids_without_package:
			line_list.append((0, 0, {
				'product_id': move_line.product_id.id,
				'move_qty': move_line.product_uom_qty,
			}))

		return {
			'name': 'Move Lines',
			'type': 'ir.actions.act_window',
			'res_model': 'stock.move.wizard',
			'view_mode': 'form',
			'target': 'new',
			'context': {
				'default_move_line_ids': line_list,			},
		}


	@api.depends('move_type', 'immediate_transfer', 'move_ids.state', 'move_ids.picking_id')
	def _compute_state(self):
		super(Picking, self)._compute_state()  # Call the original compute method
		for picking in self:
			if picking.state == 'assigned' and not picking.assigned_date:
				picking.assigned_date = fields.Datetime.now()

	def cron_alert_picking_assign_date(self):
		days_limit = self.env.company.picking_notification_days
		cutoff_date = fields.Datetime.now() - timedelta(days=days_limit)
		picking_ids = self.search([('state', '=', 'assigned'), ('assigned_date', '<=', cutoff_date)])
		template_id = self.env.ref('fischerbell_custom.email_template_picking_assigned_date', raise_if_not_found=True)
		stock_group = self.env.ref('stock.group_stock_manager', raise_if_not_found=False)
		stock_users = stock_group.users if stock_group else self.env['res.users']
		stock_emails = ", ".join([user.email for user in stock_users if user.email])
		if template_id and stock_emails:
			for picking in picking_ids:
				if picking.assigned_date:
					date_diff = fields.Datetime.now() - picking.assigned_date
					template_id.sudo().with_context(days=date_diff.days).send_mail(picking.id, email_values={'email_from': self.env.user.email, 'email_to': stock_emails})
	

