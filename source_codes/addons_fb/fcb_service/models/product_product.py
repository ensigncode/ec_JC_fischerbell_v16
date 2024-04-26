# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

class ProductProduct(models.Model):
    _inherit = "product.product"

    is_serviceable = fields.Boolean(string='Is Serviceable',related='product_tmpl_id.is_serviceable')
    required_calibration = fields.Boolean('Required Calibration',related='product_tmpl_id.required_calibration')

