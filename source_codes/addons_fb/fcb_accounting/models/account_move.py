# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.exceptions import UserError
import calendar
from datetime import date

class AccountMove(models.Model):
	_inherit = "account.move"

	@api.model
	def create(self,vals):
		res = super(AccountMove,self).create(vals)
		res._check_currency_rates()
		return res

	def write(self,vals):
		res = super(AccountMove,self).write(vals)
		if 'invoice_date' in vals or 'currency_id' in vals:
			self._check_currency_rates()
		return res

	def _check_currency_rates(self):
		for record in self:
			if not record.invoice_date or record.currency_id.is_current_company_currency == True:
				continue
			year_month = record.invoice_date.strftime('%Y-%m')
			last_day_of_month = calendar.monthrange(record.invoice_date.year, record.invoice_date.month)[1]
			currency_rates = self.env['res.currency.rate'].search([
				('name', '>=', f'{year_month}-01'),
				('name', '<=', f'{year_month}-{last_day_of_month}'),
				('currency_id', '=', record.currency_id.id),
			])
			if not currency_rates:
				raise UserError(f'Currency rates for {year_month} are not configured.')



	