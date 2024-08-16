# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _

class AccountPaymentTerm(models.Model):
    _inherit = 'account.payment.term'

    is_sales = fields.Boolean(string="For Sales")
    is_purchase = fields.Boolean(string="For Purchase")