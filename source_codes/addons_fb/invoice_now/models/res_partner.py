# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class ResPartner(models.Model):
    _inherit = "res.partner"

    applicable_invoicenow = fields.Boolean(string="Applicable for Invoicenow?")