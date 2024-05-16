import base64
from collections import OrderedDict
from datetime import datetime
from odoo import http
from odoo.exceptions import AccessError, MissingError
from odoo.http import request, Response
from odoo.tools import image_process
from odoo.tools.translate import _
from odoo.addons.portal.controllers import portal
from odoo.addons.portal.controllers.portal import pager as portal_pager
import urllib.parse


class CustomerPortal(http.Controller):
	@http.route('/purchase_order/submit_data', type='http', auth='public', website=True)
	def submit_data(self, estimated_delivery_date=None, estimated_delivery_date1=None,purchase_order_name=None,order_line=None, **post):
		purchase_order = request.env['purchase.order'].sudo().search([('name', '=', purchase_order_name)], limit=1)
		if 'purchase_order_line' in post.keys():
			order_line =  request.env['purchase.order.line'].sudo().browse(int(post['purchase_order_line']))
		redirect_url = purchase_order.access_url + '?' + urllib.parse.urlencode(
			{'access_token': purchase_order.access_token})
		if estimated_delivery_date and purchase_order_name:
			if purchase_order:
				purchase_order.write({'estimated_delivery_date': estimated_delivery_date})
				purchase_order.order_line.write({'estimated_delivery_date': estimated_delivery_date})

		if estimated_delivery_date1 and purchase_order_name and order_line:
			if purchase_order and order_line:
				order_line.write({'estimated_delivery_date': estimated_delivery_date1})

		return http.request.redirect(redirect_url)
