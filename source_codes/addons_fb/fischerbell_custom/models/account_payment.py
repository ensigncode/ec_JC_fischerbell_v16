# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api,fields, models


class AccountPayment(models.Model):
	_inherit = "account.payment"

	bank_account_no = fields.Char('Bank No')
	

	def action_post(self):
		res = super(AccountPayment, self).action_post()
		account_move_id = self.env["account.move"].browse(self._context.get("active_id"))
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
			if account_move_id and account_move_id.purchase_order_id :
				purchase_order = account_move_id.purchase_order_id
				purchase_order.payment_done_notify_buyer()
		return res


