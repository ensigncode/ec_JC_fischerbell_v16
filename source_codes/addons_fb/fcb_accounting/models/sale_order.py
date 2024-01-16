# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

class SaleOrderLine(models.Model):
	_inherit = "sale.order.line"

	@api.onchange('product_id')
	def onchange_product(self):
		for line in self:
			partner_id = line.order_id.partner_id
			if line.product_id and partner_id and partner_id.customer_taxes and partner_id.l10n_in_gst_treatment == "overseas":
				line.tax_id = [(6,0,partner_id.customer_taxes.ids)]
