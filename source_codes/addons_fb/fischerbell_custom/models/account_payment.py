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
				payment.name = self.env['ir.sequence'].next_by_code('supplier_payment_seq')
		return res


