# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from datetime import timedelta


class StockPicking(models.Model):
	_inherit = "stock.picking"

	task_id = fields.Many2one('project.task', string="Task")
	attachment_ids = fields.Many2many(
		'ir.attachment','stock_attachment_rel', string='Attachments')
	pick_up = fields.Selection([
		('pc_driver', "Pickup by Driver"),
		('pc_supplier', "Pickup by Supplier"),
	], )
	def button_validate(self):
		res = super().button_validate()
		if not self.is_to_check:
			line_ids = self.move_line_ids.filtered(lambda x: x.product_id.is_serviceable)
			for line in line_ids:
				if line.product_id.service_product_ids:
					eq_sale_id = line.picking_id.sale_id
					equipment_ids = self.env['equipment.service'].search(
						[('so_ref', '=', eq_sale_id.name), ('product_id', '=', line.product_id.id)])
					for eq_service in equipment_ids:
						eq_service.update({'serial_number': line.lot_id.name,
						                   'manufacturing_date': line.lot_id.manufacturing_date or False,
						                   'expire_date': line.lot_id.expiration_date or False})

		return res
