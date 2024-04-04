# -*- coding: utf-8 -*-

from odoo import api, fields, models
from datetime import datetime, timedelta, date
from odoo.exceptions import UserError, ValidationError
import qrcode
import io
import base64


class StockPicking(models.Model):
	_inherit = "stock.picking"

	package = fields.Char(string="Package")
	qr_code = fields.Binary(string='QR Code', compute='_generate_qr_code')
	contact_one = fields.Many2one('res.partner',string="Contact 1")
	contact_two = fields.Many2one('res.partner',string="Contact 2")
	
	@api.depends('name')
	def _generate_qr_code(self):
		for picking in self:
			qr = qrcode.QRCode(
				version=1,
				error_correction=qrcode.constants.ERROR_CORRECT_L,
				box_size=5,
				border=4,
			)
			qr.add_data(picking.name)
			qr.make(fit=True)
			img = qr.make_image(fill_color="black", back_color="white")
			buffer = io.BytesIO()
			img.save(buffer, format="PNG")
			picking.qr_code = base64.b64encode(buffer.getvalue())

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
