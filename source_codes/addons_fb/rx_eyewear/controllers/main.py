from odoo import http ,_
from odoo.http import request, content_disposition
from odoo.addons.resource.models.resource import float_to_time, HOURS_PER_DAY

from datetime import datetime, date, timedelta, time
from pytz import timezone, UTC
from odoo.tools import float_compare, format_date

import base64

lens_type = {
	'blue_ray':'BLUE RAY​',
	'photo_chromic':'PHOTOCHROMIC',
	'anti_fog': 'ANTI-FOG & BLUE RAY​'
}

class OpticianPortalController(http.Controller):


	@http.route('/optician-detail', auth='user', type='http', website=True, csrf=False)
	def optician_detail(self, **kw):
     
		optic_product_ids = request.env['product.template'].sudo().search([('is_optic','=',True)])
		company_ids = request.env['res.partner'].sudo().search([('is_company','=',True)])
		outlet_ids = request.env['outlet.detail'].sudo().search([])
		lens_types = request.env['lens.type'].sudo().search([])
		prescription_types = request.env['prescription.type'].sudo().search([])
  		
		submission_count = request.env.user.submission_count
		allow_submission = request.env.user.allow_submission
		disable_form = submission_count >= allow_submission


		if kw and request.httprequest.method == 'POST': 
			if request.env.user._is_public():
				return request.redirect("/web/login")

			partner_id = None
			if kw.get('name') and kw.get('mobile') :
				name = kw.get('name')
				mobile = kw.get('mobile')
				company = kw.get('company_id')
				company_id = request.env['res.partner'].sudo().search([('name','=',company),('is_company','=',True)],limit=1)
				
				partner_id = request.env['res.partner'].sudo().search(['|',('mobile','=',mobile),('phone','=',mobile),('name','=',name)])
				if not partner_id : 
					partner_id = request.env['res.partner'].sudo().create({
						'name' : name,
						'mobile' : mobile,
					})
				if not company_id : 
					company_id = request.env['res.partner'].sudo().create({
						'name' : company,
						'is_company' : True,
					})
			

			optician_detail_id = request.env['optician.detail'].sudo().create({
				'name' : kw.get('name') if kw.get('name') else '',
				'mobile' : kw.get('mobile') if kw.get('mobile') else '',
				'email' : kw.get('email') if kw.get('email') else '',
				'emp_no' : kw.get('emp_no') if kw.get('emp_no') else '',
				'dept_code' : kw.get('dept_code') if kw.get('dept_code') else '',
				'lens_type' : int(kw.get('lens_type')) if kw.get('lens_type') else '',
				# 'presc_type' : kw.get('presc_type') if kw.get('presc_type') else '',
				'add_on_type' : lens_type.get(kw.get('add_on_type'),'') if kw.get('add_on_type') else '',
				'product_id' : eval(kw.get('product_id', '')),
    			'company_id' : company_id.id if company_id else False,
				'sphere_left' : kw.get('sphere_left') if kw.get('sphere_left') else '',
				'cyl_left' : kw.get('cyl_left') if kw.get('cyl_left') else '',
				'axis_left' : kw.get('axis_left') if kw.get('axis_left') else '',
				'sphere_right' : kw.get('sphere_right') if kw.get('sphere_right') else '',
				'cyl_right' : kw.get('cyl_right') if kw.get('cyl_right') else '',
				'axis_right' : kw.get('axis_right') if kw.get('axis_right') else '',
				'add' : kw.get('add') if kw.get('add') else '',
				'pd' : kw.get('pd') if kw.get('pd') else '',
				'requirements' : kw.get('requirements') if kw.get('requirements') else '',
				"user_id" : request.env.uid,
				"partner_id" : partner_id.id,
				'outlet_id': eval(kw.get('outlet_id', '')),
				'sg_ht' : kw.get('sg_ht') if kw.get('sg_ht') else '',
				'add_right' : kw.get('add_right') if kw.get('add_right') else '',
				'add_left' : kw.get('add_left') if kw.get('add_left') else '',
				'pd_right' : kw.get('pd_right') if kw.get('pd_right') else '',
				'pd_left' : kw.get('pd_left') if kw.get('pd_left') else '',
				'pescription' : int(kw.get('pescription')) if kw.get('sg_ht') else '',
			})
			if optician_detail_id:
				request.env.user.sudo().write({'submission_count': request.env.user.submission_count + 1})
    
				rx_eyewear_group=request.env.ref('rx_eyewear.rx_eyewear_group')
				group_users = rx_eyewear_group.users
				mail_template=request.env.ref('rx_eyewear.optician_submission_email')
				if mail_template:
					for user in group_users:
						mail_template.email_to = user.email
						mail_template.send_mail(optician_detail_id.id, force_send=True)
                
				return request.redirect('/optician-detail')

		return request.render('rx_eyewear.opptician_detail_page_template',
							  {'optic_product_ids': optic_product_ids, 'outlet_ids': outlet_ids,
							   'lens_types': lens_types, 'prescription_types': prescription_types,
							   'disable_form': disable_form})



class Binary(http.Controller):

    @http.route('/web/binary/download_document/rx_eyewear/<model("eyewear.import.export.data"):order_line>', type='http', auth="user")
    def download_document(self, order_line, **kw):
        data = order_line.print_report_excel_data()
        filecontent = base64.b64decode(data)
        if not filecontent:
            return request.not_found()
        else:
            return request.make_response(filecontent,
                                         [('Content-Type', 'application/octet-stream'),
                                          ('Content-Disposition', content_disposition('Eyewear_template.xlsx'))])
