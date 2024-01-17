# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _

class AccountPaymentMethod(models.Model):
    _inherit = 'account.payment.method'

    @api.model
    def _get_payment_method_information(self):
        res = super()._get_payment_method_information()
        res['cash'] = {'mode': 'multi', 'domain': [('type', 'in', ['bank','cash'])]}
        res['cheque'] = {'mode': 'multi', 'domain': [('type', '=', 'bank')]}
        res['giro'] = {'mode': 'multi', 'domain': [('type', '=', 'bank')]}
        res['paynow'] = {'mode': 'multi', 'domain': [('type', '=', 'bank')]}
        return res

class AccountJournal(models.Model):
    _inherit = "account.journal"

    def _default_inbound_payment_methods(self):
        res = super()._default_inbound_payment_methods()
        if self._is_payment_method_available('cash'):
            res |= self.env.ref('fcb_accounting.account_payment_method_cash_in')
        if self._is_payment_method_available('cheque'):
            res |= self.env.ref('fcb_accounting.account_payment_method_cheque_in')
        if self._is_payment_method_available('giro'):
            res |= self.env.ref('fcb_accounting.account_payment_method_giro_in')
        if self._is_payment_method_available('paynow'):
            res |= self.env.ref('fcb_accounting.account_payment_method_paynow_in')
        return res
    
    def _default_outbound_payment_methods(self):
        res = super()._default_outbound_payment_methods()
        if self._is_payment_method_available('cash'):
            res |= self.env.ref('fcb_accounting.account_payment_method_cash_out')
        if self._is_payment_method_available('cheque'):
            res |= self.env.ref('fcb_accounting.account_payment_method_cheque_out')
        if self._is_payment_method_available('giro'):
            res |= self.env.ref('fcb_accounting.account_payment_method_giro_out')
        if self._is_payment_method_available('paynow'):
            res |= self.env.ref('fcb_accounting.account_payment_method_paynow_out')
        return res