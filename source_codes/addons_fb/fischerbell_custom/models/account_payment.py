# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api,fields, models


class AccountPayment(models.Model):
	_inherit = "account.payment"

	def action_post(self):
		res = super(AccountPayment, self).action_post()
		for payment in self:
			if payment.payment_type == 'inbound':
				payment.name = self.env['ir.sequence'].next_by_code('customer_payment_seq')
			else:
				giro_payment_method_id = self.env.ref('fcb_accounting.account_payment_method_giro_out')
				paynow_payment_method_id = self.env.ref('fcb_accounting.account_payment_method_paynow_out')
				payment_method_id = payment.payment_method_line_id.payment_method_id
				if payment_method_id.id == giro_payment_method_id.id : 
					payment.name = self.env['ir.sequence'].next_by_code('giro_payment_method_seq')
				elif payment_method_id.id == paynow_payment_method_id.id : 
					payment.name = self.env['ir.sequence'].next_by_code('paynow_payment_method_seq')
				else :
					payment.name = self.env['ir.sequence'].next_by_code('supplier_payment_seq')
		return res




class AccountPaymentTerm(models.Model):
    _inherit = 'account.payment.term'

    is_customer = fields.Boolean(string="For Customer")
    is_vendor = fields.Boolean(string="For Vendor")