# -*- coding: utf-8 -*-

from odoo import api, models, fields, _
import logging
_logger = logging.getLogger(__name__)


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
				#   Check incoming stock from purchase orders
				purchase_orders = self.env['purchase.order'].search([('state', '=', 'purchase')])

				for po in purchase_orders:
					for po_line in po.order_line:
						if po_line.product_id == product:
							product_available_date = po_line.date_planned
							product_buyer_id = po.user_id
							self.product_available_date = product_available_date
							self.product_buyer_id = product_buyer_id
							if template_id and self.user_id.login:
								template_id.sudo().send_mail(self.id, force_send=True, email_values={
									'email_from': self.product_buyer_id.email, 'email_to': self.user_id.login})
						else:
							print("\n")
		return res
