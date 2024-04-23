# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_serviceable = fields.Boolean('Is Serviceable')
    service_time = fields.Integer(string='Days')
    required_calibration = fields.Boolean('Required Calibration')
    service_reminder_days = fields.Integer(string='Service Reminder Days')
    reminder_time = fields.Integer(string='Reminder time')
    service_product_ids = fields.One2many('product.service', 'product_tmpl_id', 'Products')
    extra_product_ids = fields.Many2many('product.product',compute="_compute_product_ids")
    @api.depends('service_product_ids')
    def _compute_product_ids(self):
        for tmpl in self:
            if tmpl.service_product_ids:
                tmpl.extra_product_ids = tmpl.service_product_ids.mapped('product_variant_id').ids
            else:
                tmpl.extra_product_ids = False






