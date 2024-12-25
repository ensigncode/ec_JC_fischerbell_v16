# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models,_
from datetime import timedelta
from odoo.exceptions import UserError


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
		for picking in self:
			line_ids = picking.move_line_ids.filtered(lambda x: x.product_id.is_serviceable)
			for line in line_ids:
				if line.product_id.service_product_ids and picking.state == 'done':
					eq_sale_id = line.picking_id.sale_id
					for service in line.product_id.service_product_ids:
						if "/OUT/" in line.picking_id.name and line.picking_id.origin != False:
							equipment_ids = self.env['equipment.service'].create({'so_ref': eq_sale_id.name,
														  					'product_id': line.product_id.id,
																			'partner_id': eq_sale_id.partner_id.id,
																			'delivered_date': picking.date_done,
																			'service_product_id': service.product_variant_id.id,
																			'serial_number': line.lot_id.name,
																			'manufacturing_date': line.lot_id.manufacturing_date or False,
																			'expire_date': line.lot_id.expiration_date or False,
																			'eq_service_date': picking.date_done + timedelta(days=service.service_time),
																			'eq_reminder_date': picking.date_done + timedelta(days=(service.service_time-service.reminder_time))
																			})
		return res
