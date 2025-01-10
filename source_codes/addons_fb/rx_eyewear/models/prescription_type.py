# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _

class PrescriptionType(models.Model):
    _name = 'prescription.type'
    _description = 'Prescription Type'

    name = fields.Char(string='Name', required=True)
