# -*- coding: utf-8 -*-

from odoo import _, api, fields, models

class Channel(models.Model):
    _inherit = 'mail.channel'

    is_sales_loan_management = fields.Boolean('Loan Orders Management')
    
