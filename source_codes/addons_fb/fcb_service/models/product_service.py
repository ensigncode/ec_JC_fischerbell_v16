# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

class ProductService(models.Model):
    _name = "product.service"

    product_id = fields.Many2one('product.product','Products', domain="[('detailed_type', '=', 'service')]")
    reminder_time = fields.Integer(string='Reminder time',related='product_id.reminder_time')
    time_selection = fields.Selection([('day', 'Day'), ('month', 'Month'), ('year', 'Year')],  default='day')
    service_reminder_days = fields.Integer(string='Service Reminder Days')
    service_time = fields.Integer(string='Service Time',related='product_id.service_time')
