# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class SupplierInfo(models.Model):
    _inherit = "product.supplierinfo"

    supplier_code = fields.Char('Supplier Code', related="partner_id.supplier_code")