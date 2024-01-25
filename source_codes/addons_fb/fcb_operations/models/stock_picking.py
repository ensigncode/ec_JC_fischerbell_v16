# -*- coding: utf-8 -*-

from odoo import api, fields, models
from datetime import datetime, timedelta, date
from odoo.exceptions import UserError, ValidationError


class StockPicking(models.Model):
	_inherit = "stock.picking"

	def cron_alert_vendor_date(self):
		partner_ids = self.env['res.partner'].search([('supplier_rank', '=', True)])
		template_id = self.env.ref('fcb_operations.email_template_alert_reminder_1', raise_if_not_found=True)

		for partner in partner_ids:
			if partner.city == 'Singapore':
				local_supplier = partner
				for rec in self.search([
					('date_deadline', '<=', fields.Date.today() - timedelta(days=1)),
				]):
					if template_id and local_supplier.email:
						template_id.sudo().send_mail(rec.id, force_send=True, email_values={
							'email_from': self.env.user.email, 'email_to': local_supplier.email})

			else:
				overseas_supplier = partner
				for rec in self.search([
					('date_deadline', '<=', fields.Date.today() - timedelta(days=5)),
				]):
					if template_id and overseas_supplier.email:
						template_id.sudo().send_mail(rec.id, force_send=True, email_values={
							'email_from': self.env.user.email, 'email_to': overseas_supplier.email})
