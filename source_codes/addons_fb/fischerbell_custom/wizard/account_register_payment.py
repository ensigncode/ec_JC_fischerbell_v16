# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, RedirectWarning
from odoo.tools.misc import formatLang, format_date



class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"


    bank_account_no = fields.Char('Bank No')
    is_bank = fields.Boolean()

    @api.onchange('payment_method_line_id')
    def onchange_paymnet_method(self):
        for record in self:
            if record.payment_method_line_id.name == 'Cheque':
                record.is_bank = True
            else:
                record.is_bank = False

    def _init_payments(self, to_process, edit_mode=False):
        payments = super()._init_payments(to_process, edit_mode=edit_mode)
        for payment, vals in zip(payments, to_process):
                payment.write({'bank_account_no': self.bank_account_no})
        return payments