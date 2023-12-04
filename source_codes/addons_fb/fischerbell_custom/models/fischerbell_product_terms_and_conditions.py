# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models

class FischerbellProductTermsAndConditions(models.Model):
	_name = 'fischerbell.product.terms.and.conditions'
	_description = 'Fischerbell Product Terms and Conditions'

	name = fields.Char('Name')
	description = fields.Html(string="Terms and Conditions")
