# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

class ResPartner(models.Model):
	_inherit = "res.partner"

	customer_taxes = fields.Many2one('account.tax',domain=[('type_tax_use','=','sale')],string="Customer Taxes")
	supplier_taxes = fields.Many2one('account.tax',domain=[('type_tax_use','=','purchase')],string="Supplier Taxes")


