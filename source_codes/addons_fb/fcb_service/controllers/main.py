 # -*- coding: utf-8 -*-
from odoo.http import request, content_disposition

from odoo import fields
from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import pager
from odoo.addons.portal_signature.controllers import main


class PortalAttendanceInh(main.PortalAttendance):
	@http.route(['/my/transfer', '/my/transfer/page/<int:page>'],
				type='http', search=None, website=True)
	def my_transfer_search_sort_view(self, page=1,**kwargs):
		"""To search and filter in the list view of attendance"""
		uid = request.session.uid
		user_id = request.env['res.users'].sudo().browse(uid)
		
		search_domain = [('driver_id', '=', user_id.partner_id.id),('state','in',['assigned',])]
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

	def _generate_report(self, user_input, download=True):
		report = \
		request.env["ir.actions.report"].sudo()._render_qweb_pdf('stock.report_deliveryslip', [user_input.id],
																 data={'report_type': 'pdf'})[0]

		report_content_disposition = content_disposition('Certification.pdf')
		if not download:
			content_split = report_content_disposition.split(';')
			content_split[0] = 'inline'
			report_content_disposition = ';'.join(content_split)

		return request.make_response(report, headers=[
			('Content-Type', 'application/pdf'),
			('Content-Length', len(report)),
			('Content-Disposition', report_content_disposition),
		])

	@http.route("/my/transfer/<int:transfer_id>/print", type='http', auth="public", website=True)
	def transfer_get_certification(self, transfer_id, **kwargs):
		 transfer = request.env['stock.picking'].sudo().search([
			 ('id','=',transfer_id)
		 ])

		 if not transfer:
			 # no certification found
			 return request.redirect("/")

		 return self._generate_report(transfer, download=True)