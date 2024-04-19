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
	contact_ids = fields.Many2many('res.partner',string="Contact IDS",compute="_compute_contact_ids")
	contact_one = fields.Many2one('res.partner',string="Contact 1")
	contact_two = fields.Many2one('res.partner',string="Contact 2")
	
	@api.depends('partner_id')
	def _compute_contact_ids(self):
		for res in self : 
			parent_id = self.partner_id.parent_id if self.partner_id.parent_id else False
			if parent_id :
				partner_ids = self.env['res.partner'].sudo().search([('parent_id','=',parent_id.id)])
				res.contact_ids = partner_ids
			else :
				partner_ids = self.env['res.partner'].sudo().search([])
				res.contact_ids = partner_ids

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
		overseas_stock_picking_ids = self.env['stock.picking'].sudo().search([('state','not in',['done','cancel']),('picking_type_code','=','incoming')])
		
		partner_ids = self.env['res.partner'].search([('supplier_rank', '=', True)])
		template_id = self.env.ref('fcb_operations.email_template_alert_reminder_1', raise_if_not_found=True)
		overseas_partner_stock_picking_ids =  overseas_stock_picking_ids.filtered(lambda x:x.partner_id.l10n_in_gst_treatment == 'overseas')
		if template_id:
			if overseas_partner_stock_picking_ids:
				rest_picking_ids = overseas_stock_picking_ids.filtered(lambda x:x.id not in  overseas_partner_stock_picking_ids.ids)
				today_date = date.today()
				start_date = today_date - timedelta(days=5)
				end_date = today_date
				for picking in overseas_partner_stock_picking_ids.filtered(lambda x:start_date < x.date_deadline.date() and x.date_deadline.date()  <= end_date or  x.date_deadline.date() < today_date):
					e1 = template_id.sudo().send_mail(picking.id, force_send=True, email_values={'email_from': self.env.user.email, 'email_to': picking.partner_id.email})
			if rest_picking_ids :
				rest_picking_ids = overseas_stock_picking_ids
				for picking in rest_picking_ids:
					today_date = date.today()
					start_date = today_date - timedelta(days=1)
					end_date = today_date 
					for picking in overseas_partner_stock_picking_ids.filtered(lambda x:start_date < x.date_deadline.date() and x.date_deadline.date()  <= end_date  or  x.date_deadline.date() < today_date):
						e2 = template_id.sudo().send_mail(picking.id, force_send=True, email_values={'email_from': self.env.user.email, 'email_to': picking.partner_id.email})

		# for picking_id in overseas_stock_picking_ids :
		# 	if picking_id.partner_id.l10n_in_gst_treatment == 'overseas' :
		# 		overseas_supplier = picking_id.partner_id
		# 		# for rec in self.search([('date_deadline', '<=', fields.Date.today() - timedelta(days=5))]):
		# 		print("\n\n overseas supplier rec ===== ",rec)
		# 		if template_id and overseas_supplier.email:
		# 			template_id.sudo().send_mail(rec.id, force_send=True, email_values={
		# 			'email_from': self.env.user.email, 'email_to': overseas_supplier.email})
		# 	else :
		# 		local_supplier = picking_id.partner_id
		# 		for rec in self.search([('date_deadline', '<=', fields.Date.today() - timedelta(days=1))]):
		# 			print("\n\n rec local supplier ===== ",rec)
		# 			if template_id and local_supplier.email:
		# 				template_id.sudo().send_mail(rec.id, force_send=True, email_values={
		# 					'email_from': self.env.user.email, 'email_to': local_supplier.email})
		
		
		
