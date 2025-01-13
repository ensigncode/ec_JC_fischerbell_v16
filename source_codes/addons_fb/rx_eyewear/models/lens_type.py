# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _

class LensType(models.Model):
    _name = 'lens.type'
    _description = 'Lens Type'

    name = fields.Char(string='Name', required=True)
