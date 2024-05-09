# -*- coding: utf-8 -*-

from odoo import api, models, fields, _


class SaleOrder(models.Model):
	_inherit = 'sale.order'

	product_available_date = fields.Date("Product Available Date")
	product_buyer_id = fields.Many2one('res.users')

	def action_confirm(self):
		res = super(SaleOrder, self).action_confirm()
		template_id = self.env.ref('fcb_operations.email_template_available_quantity_reminder', raise_if_not_found=True)

		for order_line in self.order_line:
			product = order_line.product_id
			qty_to_deliver = order_line.product_uom_qty
			stock_available = product.qty_available

			if stock_available < qty_to_deliver:
				purchase_line_orders = self.env['purchase.order.line'].search([('product_id', '=', product.id)])
				for po_line in purchase_line_orders:
					if po_line.product_id.id == product.id:
						product_available_date = po_line.estimated_delivery_date
						product_buyer_id = po_line.order_id.user_id
						self.product_available_date = product_available_date
						self.product_buyer_id = product_buyer_id

						if template_id and self.user_id.login:
							template_values = {
								'email_from': product_buyer_id.email,
								'email_to': self.user_id.partner_id.email,
							}
							template_id.sudo().send_mail(self.id, force_send=True, email_values=template_values)

		return res
