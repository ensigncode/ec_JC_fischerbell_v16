# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from datetime import timedelta
import pytz

class ProductService(models.Model):
    _name = "product.service"

    reminder_time = fields.Integer(string='Reminder time',)
    service_reminder_days = fields.Integer(string='Service Reminder Days')
    service_time = fields.Integer(string='Service Time',)
    product_tmpl_id = fields.Many2one('product.template','Products')
    product_ids = fields.Many2many('product.product')
    extra_product_ids = fields.Many2many('product.product',related="product_tmpl_id.extra_product_ids")
    product_variant_id = fields.Many2one('product.product','Products', domain="[('detailed_type', '=', 'service'),('id','not in',extra_product_ids)]")
    equipment_id = fields.Many2one('equipment.service','equipment service')
    service_date = fields.Datetime(string='Service Time',)
    reminder_date = fields.Datetime(string='Service Time',)