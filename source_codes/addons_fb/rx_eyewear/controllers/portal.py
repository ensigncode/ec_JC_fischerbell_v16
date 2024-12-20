# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http
from odoo.http import request
from odoo.tools import date_utils
from odoo.addons.portal.controllers import portal
from odoo.addons.portal.controllers.portal import pager


class PortalOpticianDetail(portal.CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super(PortalOpticianDetail, self)._prepare_home_portal_values(
			counters)
        uid = request.session.uid
        user_id = request.env['res.users'].sudo().browse(uid)
        optician_detail_count = 0
        values = {}
        if user_id :
            optician_detail_count = request.env['optician.detail'].sudo().search_count(
				[('user_id', '=', user_id.id)])
            values.update({
				'optician_detail_count': optician_detail_count,
			})
        return values

    @http.route(['/my/optician-detail', '/my/optician-detail/page/<int:page>'],
                type='http',auth="user", website=True)
    def optician_detail_portal_view(self, page=1,**kwargs):
        """To search and filter in the list view of attendance"""
        uid = request.session.uid
        user_id = request.env['res.users'].sudo().browse(uid)
        
        search_domain = [('user_id', '=', user_id.id)]
       
        optician_detail_id = request.env['optician.detail'].sudo().search([])
        total_optician_detail = optician_detail_id.sudo().search_count([('user_id', '=', user_id.id)])
        page_detail = pager(url='/my/optician-detail',
                            total=total_optician_detail,
                            page=page,
                            step=10)
        
        optician_detail = optician_detail_id.sudo().search(
            search_domain,
            limit=10,
            offset=page_detail['offset'])
        print("\n\n optician_detail === ",optician_detail)
        vals = {
            'optician_detail': optician_detail,
            'page_name': 'optician_detail',
            'pager': page_detail,
            'default_url': '/my/optician-detail',
        }
        return request.render("rx_eyewear.portal_optician_detail_list", vals)