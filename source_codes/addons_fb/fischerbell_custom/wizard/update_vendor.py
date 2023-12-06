# -*- coding: utf-8 -*-
from odoo import fields, models, api


class WizVendors(models.TransientModel):
	_name = 'update.product.vendor'
	_description = 'Add custom vendors in product'

	partner_id = fields.Many2one('res.partner', string="Product Vendors",)
	product_qty = fields.Float('Quantity')

	def confirm(self):
		if self._context.get('order_id'):
			order_id = self.env['sale.order'].browse(self._context['order_id'])
			product_id = order_id.order_line and order_id.order_line[0].product_id

			if product_id:
				seller_info = (0, 0, {'partner_id': self.partner_id.id, 'min_qty': self.product_qty})
				product_id.write({'seller_ids': [seller_info]})

			order_id.action_confirm()


