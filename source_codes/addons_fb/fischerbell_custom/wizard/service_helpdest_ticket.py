# -*- coding: utf-8 -*-
from odoo import fields, models, api


class ServiceHelpdeskTicket(models.TransientModel):
	_name = 'service.helpdesk.ticket'
	_description = 'Service Helpdesk Ticket'

	service_priority = fields.Selection([
		('urgent', 'Urgent'),
		('express', 'Express'),
		('standard', 'Standard'),
	])
	shipping_type = fields.Selection([
		('pickup', 'Pickup'),
		('self_drop', 'Self Drop'),
	])
	sale_id = fields.Many2one('sale.order', string='Sale Order')
	partner_id = fields.Many2one('res.partner', string='Customer')
	date_of_request = fields.Datetime("Date of Request")

	def action_submit_ticket(self):
		self.ensure_one()
		sale_id = self.sale_id
		ticket_vals = {
			'name': f"Service Ticket for {sale_id.partner_id.name}",
			'partner_id': sale_id.partner_id.id,
			'partner_name': sale_id.partner_id.name,
			'partner_email': sale_id.partner_id.email,
			'partner_phone': sale_id.partner_id.phone,
			'shipping_type': self.shipping_type,
			'service_priority': self.service_priority,
			'date_of_request': self.date_of_request,
			'user_id': self.env.user.id,
			'sale_id': sale_id.id,
			'service_line': [(0, 0, {
				'product_id': sale_id.equipment_service_id.product_id.id,
				'product_uom_qty': 1,
			})],
		}
		self.env['helpdesk.ticket'].create(ticket_vals)
		return {'type': 'ir.actions.act_window_close'}
