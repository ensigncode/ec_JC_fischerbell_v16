# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

class PurchaseOrderLine(models.Model):
	_inherit = "purchase.order.line"

	def _compute_tax_id(self):
		res = super()._compute_tax_id()
		for line in self:
			partner_id = line.order_id.partner_id
			if line.product_id and partner_id and partner_id.supplier_taxes and partner_id.l10n_in_gst_treatment == "overseas":
				line.taxes_id = [(6,0,partner_id.supplier_taxes.ids)]
		return res