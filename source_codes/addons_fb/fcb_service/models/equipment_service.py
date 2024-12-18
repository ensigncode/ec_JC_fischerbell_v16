# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from datetime import timedelta
import pytz


class EquipmentService(models.Model):
	_name = "equipment.service"
	_rec_name = 'partner_id'

	partner_id = fields.Many2one('res.partner', string="Customer ")
	product_id = fields.Many2one('product.product', string="Product")
	delivered_date = fields.Datetime(string="Equipment Purchase Date")
	sale_id = fields.Many2one('sale.order', string="Sale Order")
	serial_number = fields.Char(string='Serial Number')
	so_ref = fields.Char(string='So Ref')
	categ_id = fields.Many2one('product.category', 'Product Category', readonly=True)
	expire_date = fields.Datetime('Expire Date')
	manufacturing_date = fields.Datetime('Manufacturing Date')
	is_inhouse_service = fields.Boolean("Is Inhouse Service ?")
	product_variant_id = fields.Many2one('product.product', 'Products', )
	eq_service_date = fields.Datetime(string='Service Date', )
	eq_reminder_date = fields.Datetime(string='Reminder Date', )
	service_product_id = fields.Many2one('product.product', string="Service Product", domain="[('detailed_type', '=', 'service')]")
	quotation_count = fields.Integer( string='Quotations Count',compute='_compute_quotation_count')
	def _compute_quotation_count(self):
		for record in self:
			sale_orders = self.env['sale.order'].search([('equipment_service_id', '=', record.id)])
			record.quotation_count = len(sale_orders)
	def action_view_quotation(self):
		self.ensure_one()
		sale_orders = self.env['sale.order'].search([('equipment_service_id', '=', self.id)])
		if sale_orders:
			return {
				'type': 'ir.actions.act_window',
				'name': 'Quotation',
				'res_model': 'sale.order',
				'view_mode': 'form',
				'view_id': self.env.ref('sale.view_order_form').id,
				'res_id': sale_orders[0].id,
				'target': 'current',
			}
	def action_create_quotation(self):
		for record in self:
			record.env['sale.order'].create({
				'partner_id': record.partner_id.id,
				'date_order': fields.Date.today(),
				'equipment_service_id': record.id,
				'order_line': [(0, 0, {
					'product_id': record.service_product_id.id,
					'name': record.service_product_id.name,
					'product_uom_qty': 1,
					'price_unit': record.service_product_id.lst_price,
				})],
			})

	@api.onchange('product_id')
	def onchange_product_id(self):
		for record in self:
			record.categ_id = record.product_id.categ_id.id or False

	def _send_reminder_emails(self):
		equipment_records = self.env['equipment.service'].search([])
		utc_now = fields.Datetime.now().astimezone(pytz.utc).date()  # Get current date in UTC
		for record in equipment_records:
			if record.partner_id and record.is_inhouse_service:
				if record.eq_reminder_date:
					reminder_date = record.eq_reminder_date.date()
					if reminder_date == utc_now:
						body = f"""Hello {record.partner_id.name},<br>
                                    <p> your service for {record.service_product_id.name or ''} is due on {record.eq_reminder_date.strftime('%d-%m-%Y') or ''} 
                                    please contect sales team to get quote.</p>
                                    <p>Regards,</p>
                                    <p>{record.env.company.name or ''}</p>
                            						"""
						mails = {
							'subject': "Service Reminder Email",
							'email_from': self.env.user.email,
							'email_to': record.partner_id.email,
							'body_html': body,
							'auto_delete': False,
						}
						mail = self.env['mail.mail'].create(mails)
						mail.send()

	def name_get(self):
		if self._context.get("model_name") == 'project.task':
			return [(rec.id, '%s' % (rec.serial_number)) for rec in self]
		else:
			return super(EquipmentService, self).name_get()
