# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api,fields, models
from odoo.exceptions import UserError, ValidationError

class FischerbellProductBrand(models.Model):
	_name = 'fischerbell.product.brand'
	_description = 'Product Brand'

	name = fields.Char('Name')
