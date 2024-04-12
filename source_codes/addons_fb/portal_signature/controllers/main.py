 # -*- coding: utf-8 -*-

import pytz
from collections import OrderedDict
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import fields
from odoo import http
from odoo.http import request
from odoo.tools import date_utils
from odoo.addons.portal.controllers import portal
from odoo.addons.portal.controllers.portal import pager
from odoo.exceptions import UserError, ValidationError
import base64


class PortalAttendance(portal.CustomerPortal):
	def _prepare_home_portal_values(self, counters):
		"""To get the count of the attendance in portal"""
		values = super(PortalAttendance, self)._prepare_home_portal_values(
			counters)
		uid = request.session.uid
		user_id = request.env['res.users'].sudo().browse(uid)
		transfer_count = 0
		if user_id and user_id.partner_id:
			transfer_count = request.env['stock.picking'].sudo().search_count(
				[('driver_id', '=', user_id.partner_id.id)])
			values.update({
				'transfer_count': transfer_count,
			})
		return values
	@http.route(['/my/transfer', '/my/transfer/page/<int:page>'],
				type='http',search=None, website=True)
	def my_transfer_search_sort_view(self, page=1,**kwargs):
		"""To search and filter in the list view of attendance"""
		uid = request.session.uid
		user_id = request.env['res.users'].sudo().browse(uid)
		
		search_domain = [('driver_id', '=', user_id.partner_id.id),('state','in',['assigned','done'])]
		picking_obj = request.env['stock.picking'].sudo().search(
			[])
		total_picking = picking_obj.sudo().search_count(
			[('driver_id', '=', user_id.partner_id.id)] + search_domain)
		page_detail = pager(url='/my/transfer',
							total=total_picking,
							page=page,
							step=10)
		
		picking_id = picking_obj.sudo().search(
			search_domain,
			limit=10,
			offset=page_detail['offset'],
			order='id desc' 
			)
		vals = {
			'current_date' : fields.date.today(),
			'picking_ids': picking_id,
			'page_name': 'transfer',
			'pager': page_detail,
			'default_url': '/my/transfer',
		}
		return request.render("portal_signature.portal_list_transfer", vals)

	@http.route(['/my/transfer/<int:picking_id>', '/my/transfer/<int:picking_id>/page/<int:page>'], type='http', auth="public", website=True)
	def portal_my_transfer(self, picking_id=None, access_token=None, page=1, date_begin=None, date_end=None, sortby=None, search=None, search_in='content', groupby=None, task_id=None, **kw):
		
		picking_sudo = request.env['stock.picking'].sudo().browse(picking_id)
		values = {
			'transfer': picking_id,
			'picking_id':picking_sudo,
			'page_name': 'transfer',
			'default_url': '/my/transfer',
			}
		return request.render("portal_signature.portal_my_transfer_detail", values)

	@http.route(['/my/need_approved'], type='json', auth="public", website=True)
	def portal_transfer_accept(self,*args, **kwargs):
		current_url = http.request.httprequest.full_path
		attachments = []
		context = {}
		picking = False
		if 'picking_id' in current_url:
			picking = int(current_url.split('=')[-1])
		access_token=None
		name=None
		signature=None
		name = ""
		if 'signature' in kwargs and kwargs.get('signature'):
			signature = kwargs.get('signature')
		if 'name' in kwargs and kwargs.get('name'):
			name = kwargs.get('name')
		picking_id = request.env['stock.picking'].sudo().browse(picking)
		current_datetime = datetime.now()
		picking_id.write({'signature':signature,'signed_on':current_datetime,'signed_by':name,'signature_uploded':True})
		self.successfull_delivery = True
		quality_id = request.env['quality.check'].sudo().search([('picking_id','=',picking_id.id)])
		if quality_id:
			quality_id.do_pass()
		picking_id.sudo().make_picking_done()

		if picking_id and picking_id.picking_type_code == 'outgoing' :
			if picking_id.partner_id.parent_id : 
				parent_id = picking_id.partner_id.parent_id
				context.update({
					'platform_name' : parent_id.platform_name,
				})
			sale_order_id = request.env['sale.order'].sudo().search([('name','=',picking_id.origin)])
			invoices = False
			if sale_order_id : 
				if not sale_order_id.invoice_ids :
					invoices = sale_order_id._create_invoices()
					invoices.sudo().action_post()
				else :
					sale_order_id.invoice_ids.action_post()
					invoices = sale_order_id.invoice_ids
			for invoice in invoices:
				pdf = request.env['ir.actions.report'].sudo()._render_qweb_pdf('account.account_invoices', [invoice.id])
				pdf_base64 = base64.b64encode(pdf[0])
				attachment = request.env['ir.attachment'].sudo().create({
					'name': invoice._get_report_base_filename(),
					'datas': pdf_base64,
					'type': 'binary',
					'res_model': 'account.move',
					'res_id': picking_id.id
				})
				attachments.append((4, attachment.id))
			pdf = request.env['ir.actions.report'].sudo()._render_qweb_pdf('stock.action_report_delivery', [picking_id.id])
			pdf_base64 = base64.b64encode(pdf[0])
			
			attachment = request.env['ir.attachment'].sudo().create({
				'name': 'Delivery Order - %s - %s' % (picking_id.partner_id.name or '', picking_id.name),
				'datas': pdf_base64,
				'type': 'binary',
				'res_model': 'stock.picking',  
				'res_id': picking_id.id
			})
			attachments.append((4, attachment.id))
			
			template = request.env.ref('portal_signature.email_template_successfull_delivery_notification')
			sale_manager_group_id = request.env.ref('sales_team.group_sale_manager')
			sale_managers = request.env['res.users'].sudo().search([('groups_id', 'in', sale_manager_group_id.ids)])
			email_addresses = sale_managers.mapped('email')
			email_cc = ','.join(email_addresses)
			email_values = {
				'email_from': request.env.user.email_formatted,
				'email_cc': email_cc,
				'auto_delete': False,
				'email_to' : picking_id.partner_id.email if picking_id.partner_id.email else '',
				'attachment_ids': attachments,
			}
			try:
				template.with_context(**context).sudo().send_mail(picking_id.id,force_send=True, raise_exception=False, email_values=email_values)
			except Exception as e:
				raise UserError(_("Error : %s") % e)

		return {
			'force_refresh': True,
		}