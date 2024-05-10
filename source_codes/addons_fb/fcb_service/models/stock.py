# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from datetime import timedelta


class StockPicking(models.Model):
	_inherit = "stock.picking"


	task_id = fields.Many2one('project.task', string="Task")
	attachment_ids = fields.Many2many(
		'ir.attachment','stock_attachment_rel', string='Attachments')
	def button_validate(self):
		res = super().button_validate()
		if not self.is_to_check:
			line_ids = self.move_line_ids.filtered(lambda x: x.product_id.is_serviceable)
			for line in line_ids:
				if line.product_id.service_product_ids:
					equipment_service_vals = {
						'product_id': line.product_id.id,
						'serial_number': line.lot_id.name,
						'partner_id': self.partner_id.id,
						'so_ref': self.origin,
						'manufacturing_date': line.lot_id.manufacturing_date,
						'expire_date': line.lot_id.expiration_date,
						'categ_id': line.product_id.categ_id.id,
						'delivered_date': self.date_done,
					}
					move_lines = []
					for service in line.product_id.service_product_ids:
						move_line = (0, 0, {
							'product_variant_id': service.product_variant_id.id or False,
							'name': service.product_variant_id.name,
							'product_uom_qty': 1,
						})
						move_lines.append(move_line)
					equipment_service_vals.update({'service_product_ids': move_lines})
				self.env['equipment.service'].create(equipment_service_vals)
		return res
