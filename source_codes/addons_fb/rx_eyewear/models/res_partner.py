# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from io import BytesIO
import xlwt
import base64
from odoo.tools.misc import xlsxwriter

class ResPartner(models.Model):
    _inherit = 'res.partner'

    total_budget = fields.Float('Eyewaer Budget')
    product_eyewaer_ids = fields.Many2many('product.product', domain=[('is_optic', '=', True)], string='EyeWear Products')


