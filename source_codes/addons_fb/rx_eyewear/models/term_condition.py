# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from io import BytesIO
import xlwt
import base64
from odoo.tools.misc import xlsxwriter
from odoo.exceptions import ValidationError

class TermsConditions(models.Model):
    _name = 'optician.term.condition'
    _description = 'Terms Conditions'

    name = fields.Char()

    def unlink(self):
        for record in self:
            raise ValidationError(_("You Cannot not delete Terms & Conditions !!"))
        res = super().unlink()
        return res