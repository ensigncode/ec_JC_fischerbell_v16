# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http
from odoo.http import request
from odoo.tools import date_utils
from odoo.addons.portal.controllers import portal
from odoo.addons.portal.controllers.portal import pager
from datetime import datetime



class CustomerESign(portal.CustomerPortal):

    @http.route(['/customer/e-sgin'], type='http', auth="public", website=True)
    def customer_esign_page(self, **kwargs):
        sale_id = False
        if kwargs.get('sale_id'):
            sale_id = int(kwargs.get('sale_id'))
        sale_id = request.env['sale.order'].sudo().browse(sale_id)
        return request.render('customer_capture_sign.customer_esign_page_template', {'sale_id': sale_id})

    
    @http.route(['/customer/esign'], type='json', auth="public", website=True)
    def customer_esign(self,*args, **kwargs):

        current_url = http.request.httprequest.full_path
        sale_id = False
        if 'sale_id' in current_url:
            sale_id = int(current_url.split('=')[-1])
        access_token=None
        name=None
        signature=None
        name = ""

        if 'signature' in kwargs and kwargs.get('signature'):
            signature = kwargs.get('signature')
        if 'name' in kwargs and kwargs.get('name'):
            name = kwargs.get('name')

        sale_id = request.env['sale.order'].sudo().browse(sale_id)
        current_datetime = datetime.now()
        sale_id.write({'signature':signature,'signed_on':current_datetime,'signed_by':name})
        return {
            'force_refresh': True,
            'redirect_url':'/thankyou-sign',
        }