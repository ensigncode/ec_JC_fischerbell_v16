# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from datetime import datetime, date
from odoo.exceptions import UserError, ValidationError

class DeliveryOrderWithTraining(models.Model):
	_name = 'delivery.order.with.training'
	_description = 'Delivery Order With Training'

	partner_id = fields.Many2one('res.partner', 'Customer')
	sale_id = fields.Many2one('sale.order', 'Sale Order')
	picking_id = fields.Many2one('stock.picking', 'Stock Picking')

	@api.model
	def default_get(self,fields):
		res = super(DeliveryOrderWithTraining, self).default_get(fields)
		context = dict(self._context or {})
		active_id = [context['active_id']]
		sale_order_obj = self.env['sale.order']
		order_line = []
		sale = sale_order_obj.browse(active_id)

		for line in sale.order_line:
				lines = {
					'sale_line_id': line.id,
					'product_id': line.product_id.id,
					'description': line.name,
					'quantity': line.product_uom_qty
				}
				order_line.append((0,0,lines))
				
		res.update({
			'partner_id': sale.partner_id,
			'sale_id': sale.id,
		})

		return res

	def action_print_delivery_order(self):
		picking = self.picking_id

		return self.env.ref('fischerbell_custom.action_report_delivery_order_training').report_action(picking.id)