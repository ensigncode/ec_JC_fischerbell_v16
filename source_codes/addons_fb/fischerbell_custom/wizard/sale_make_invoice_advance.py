# -*- coding: utf-8 -*-
import calendar
from odoo import api, fields, models, _
from datetime import datetime, timedelta
import json

class SaleAdvancePaymentInv(models.TransientModel):
	_inherit = "sale.advance.payment.inv"

	def _prepare_invoice_values(self, order, name, amount, so_line):
		invoice_vals = super()._prepare_invoice_values(order, name, amount, so_line)
		invoice_vals['narration'] = f"Terms and Conditions"
		return invoice_vals
