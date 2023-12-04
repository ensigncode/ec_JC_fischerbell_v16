# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api,fields, models
from odoo.exceptions import UserError, ValidationError

class FischerbellSaleTermsAndConditions(models.Model):
	_name = 'fischerbell.sale.terms.and.conditions'
	_description = 'Fischerbell Sale Terms and Conditions'

	name = fields.Char('Name')
	type = fields.Selection([
		('quotation', 'Quotation'),
		('sale', 'Sale Order'),
		('loan', 'Loan Order'),
		('exchange', 'Exchange Order'),
		('training', 'Training'),
		('replacement', 'Replacement Order')
	])
	note = fields.Html('Terms and Conditions')
