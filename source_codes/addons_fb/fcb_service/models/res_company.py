# -*- coding: utf-8 -*-

from odoo import api, models, fields

class ResCompany(models.Model):
    _inherit = 'res.company'

    company_stamp = fields.Binary("Company Stamp")
