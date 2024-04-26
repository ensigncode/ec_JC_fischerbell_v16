# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from datetime import timedelta


class StockPicking(models.Model):
	_inherit = "stock.picking"


	task_id = fields.Many2one('project.task', string="Task")

	def button_validate(self):
		res = super().button_validate()
		if not self.is_to_check:
			line_ids = self.move_line_ids.filtered(lambda x: x.product_id.is_serviceable)
			line_id = []
			equipment_services = []
			for line in line_ids:
				if line.id not in line_id:
					line_id.append(line.id)
					equipment_service_vals = {
						'product_id': line.product_id.id,
						'lot_id': line.lot_id.id,
						'partner_id': self.partner_id.id,
						'so_ref': self.origin,
						'manufacturing_date': line.lot_id.manufacturing_date,
						'expire_date': line.lot_id.expiration_date,
						'categ_id': line.product_id.categ_id.id,
						'service_date': self.date_done + timedelta(
							days=line.product_id.service_time) if self.date_done else False,
						'delivered_date': self.date_done,
					}
					if equipment_service_vals['service_date']:
						equipment_service_vals['service_reminder_date'] = equipment_service_vals[
							                                                  'service_date'] - timedelta(
							days=line.product_id.service_reminder_days)
					else:
						equipment_service_vals['service_reminder_date'] = False
					equipment_services.append(equipment_service_vals)

			self.env['equipment.service'].create(equipment_services)
		return res

