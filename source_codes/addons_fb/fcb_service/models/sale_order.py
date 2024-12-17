# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from datetime import timedelta


class SaleOrder(models.Model):
	_inherit = "sale.order"

	service_product_ids = fields.One2many('product.service', 'sale_product_tmp_id', 'Service Products')
	have_special_permission = fields.Boolean("Proforma Invoices")
	have_special_permission_note = fields.Text(string='Description', required=False)
	equipment_service_id = fields.Many2one('equipment.service', string='Equipment Service')

	@api.model_create_multi
	def create(self, vals_list):
		res = super().create(vals_list)
		for record in res:
			if record.order_line:
				for product_line in record.order_line:
					if product_line.product_id.service_product_ids:
						move_lines = []
						for service_product in product_line.product_id.service_product_ids:
							service_date = (record.date_order.date() + timedelta(
								days=service_product.service_time))
							reminder_date = service_date - timedelta(days=service_product.reminder_time)
							move_line = (0, 0, {
								'product_variant_id': product_line.product_id.id or False,
								'service_date': service_date,
								'reminder_date': reminder_date,
								'service_product_id':  service_product.product_variant_id.id,
							})
							move_lines.append(move_line)
						record.update({'service_product_ids': move_lines})
		return res

	def action_to_approve(self):
		res = super(SaleOrder, self).action_to_approve()
		# picking_ids = self.picking_ids.fillter
		# print('vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv',equipment_records)
		for record in self:
			if record.service_product_ids:
				for service in record.service_product_ids:
					equipment_service_vals = {
						'product_id': service.product_variant_id.id,
						'service_product_id': service.service_product_id.id,
						# 'serial_number': line.lot_id.name,
						'partner_id': self.partner_id.id,
						'so_ref': self.name,
						# 'manufacturing_date': line.lot_id.manufacturing_date,
						# 'expire_date': line.lot_id.expiration_date,
						'categ_id': service.product_variant_id.categ_id.id,
						'delivered_date': self.date_order,
						'eq_service_date': service.service_date,
						'eq_reminder_date': service.reminder_date,
					}
					self.env['equipment.service'].create(equipment_service_vals)
		return res
