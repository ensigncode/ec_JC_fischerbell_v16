# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_serviceable = fields.Boolean('Is Serviceable')
    service_time = fields.Integer(string='Days')
    required_calibration = fields.Boolean('Required Calibration')
    service_reminder_days = fields.Integer(string='Service Reminder Days')






