# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from io import BytesIO
import xlwt
import base64
from odoo.tools.misc import xlsxwriter

class TermsConditions(models.Model):
    _name = 'fee.eyewear'
    _description = 'Fee Eyewear'

    name = fields.Char()
