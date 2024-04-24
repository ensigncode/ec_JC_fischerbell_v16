# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

class ProductService(models.Model):
    _name = "product.service"

    reminder_time = fields.Integer(string='Reminder time',)
    time_selection = fields.Selection([('day', 'Day'), ('month', 'Month'), ('year', 'Year')],  default='day')
    service_reminder_days = fields.Integer(string='Service Reminder Days')
    service_time = fields.Integer(string='Service Time',)
    product_tmpl_id = fields.Many2one('product.template','Products')
    product_ids = fields.Many2many('product.product')
    extra_product_ids = fields.Many2many('product.product',related="product_tmpl_id.extra_product_ids")
    product_variant_id = fields.Many2one('product.product','Products', domain="[('detailed_type', '=', 'service'),('id','not in',extra_product_ids)]")

