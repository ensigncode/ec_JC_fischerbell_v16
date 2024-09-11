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


class SaleOrder(models.Model):
	_inherit = "sale.order"
	@api.depends('partner_id')
	def _compute_payment_term_id(self):
		is_sales = self.env['account.payment.term'].search([('is_sales','=',True)],limit=1).id
		for order in self:
			order = order.with_company(order.company_id)
			order.payment_term_id = is_sales