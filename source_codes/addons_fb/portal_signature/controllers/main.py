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
		
		search_domain = [('driver_id', '=', user_id.partner_id.id)]
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
			'picking': picking_id,
			'picking_id':picking_sudo,
			'page_name': 'transfer',
			}
		return request.render("portal_signature.portal_my_transfer_detail", values)

	@http.route(['/my/need_approved'], type='json', auth="public", website=True)
	def portal_transfer_accept(self,*args, **kwargs):
		current_url = http.request.httprequest.full_path
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
		picking_id.sudo().make_picking_done()

		return {
			'force_refresh': True,
		}