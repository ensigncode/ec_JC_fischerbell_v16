# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _

class AccountAsset(models.Model):
    _inherit = 'account.asset'

    asset_tagging_code = fields.Char(string="Asset Tagging code")