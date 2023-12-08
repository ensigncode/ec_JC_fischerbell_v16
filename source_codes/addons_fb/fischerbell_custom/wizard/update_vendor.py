# -*- coding: utf-8 -*-
from odoo import fields, models, api


class WizVendors(models.TransientModel):
	_name = 'update.product.vendor'
	_description = 'Add custom vendors in product'

	partner_id = fields.Many2one('res.partner', string="Product Vendors",domain=[('supplier_rank','>', 0)])
	product_qty = fields.Float('Quantity')

	def confirm(self):
		if self._context.get('order_id'):
			order_id = self.env['sale.order'].browse(self._context['order_id'])

			if self._context.get('line_ids'):
				product_ids = self.env['sale.order.line'].browse(self._context.get('line_ids')).mapped('product_id')
				for product in product_ids:
					seller_info = (0, 0, {'partner_id': self.partner_id.id, 'min_qty': self.product_qty})
					product.write({'seller_ids': [seller_info]})

			order_id.action_confirm()