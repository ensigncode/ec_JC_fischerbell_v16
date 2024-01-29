# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ProductTemplate(models.Model):
	_inherit = "product.template"

	product_length = fields.Float(string='Length')
	width = fields.Float(string='Width')
	height = fields.Float(string='Height')
	product_length_id = fields.Many2one('uom.uom', string="Length Unit")
	width_id = fields.Many2one('uom.uom', string="Width Unit")
	height_id = fields.Many2one('uom.uom', string="Height Unit")
