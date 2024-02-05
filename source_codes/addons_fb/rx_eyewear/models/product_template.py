# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_optic = fields.Boolean(string="Is Optic?")

