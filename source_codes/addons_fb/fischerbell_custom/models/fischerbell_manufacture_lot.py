# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api,fields, models
from odoo.exceptions import UserError, ValidationError

class FischerbellManufactureLot(models.Model):
	_name = 'fischerbell.manufacture.lot'
	_description = 'Fischerbell Manufacture Lot'

	name = fields.Char('Manufacture No')
	partner_id = fields.Many2one('res.partner', 'Manufacturer')
	manufacture_lot_line_ids = fields.One2many('fischerbell.manufacture.lot.line','manufacture_lot_id', string="Product Lines")

class FischerbellManufactureLotLine(models.Model):
	_name = 'fischerbell.manufacture.lot.line'

	name = fields.Char('Name')
	manufacture_lot_id = fields.Many2one('fischerbell.manufacture.lot', 'Parent')
	product_tmpl_id = fields.Many2one('product.template', 'Product')