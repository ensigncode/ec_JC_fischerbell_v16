from odoo import http ,_
from odoo.http import request
from odoo.addons.resource.models.resource import float_to_time, HOURS_PER_DAY

from datetime import datetime, date, timedelta, time
from pytz import timezone, UTC
from odoo.tools import float_compare, format_date

class OpticianPortalController(http.Controller):


	@http.route('/optician-detail', auth='public', type='http', website=True, csrf=False)
	def optician_detail(self, **kw):
		optic_product_ids = request.env['product.template'].sudo().search([('is_optic','=',True)])
		company_ids = request.env['res.partner'].sudo().search([('is_company','=',True)])
		
		
		if kw and request.httprequest.method == 'POST': 
			if request.env.user._is_public():
				return request.redirect("/web/login")

			partner_id = None
			if kw.get('name') and kw.get('mobile') :
				name = kw.get('name')
				mobile = kw.get('mobile')
				company = kw.get('company_id')
				company_id = request.env['res.partner'].sudo().search([('name','ilike',company),('is_company','=',True)],limit=1)
				
				partner_id = request.env['res.partner'].sudo().search(['|',('mobile','=',mobile),('phone','=',mobile),('name','ilike',name)])
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
				'lens_type' : kw.get('lens_type') if kw.get('lens_type') else '',
				'presc_type' : kw.get('presc_type') if kw.get('presc_type') else '',
				'add_on_type' : kw.get('add_on_type') if kw.get('add_on_type') else '',
				'product_id' : kw.get('product_id') if kw.get('product_id') else '',
				'company_id' : company_id.id if company_id else Fal,
				'sphere_left' : kw.get('sphere_left') if kw.get('sphere_left') else '',
				'cyl_left' : kw.get('cyl_left') if kw.get('cyl_left') else '',
				'axis_left' : kw.get('axis_left') if kw.get('axis_left') else '',
				'sphere_right' : kw.get('sphere_right') if kw.get('sphere_right') else '',
				'cyl_right' : kw.get('cyl_right') if kw.get('cyl_right') else '',
				'axis_right' : kw.get('axis_right') if kw.get('axis_right') else '',
				'add' : kw.get('add') if kw.get('add') else '',
				'pd' : kw.get('pd') if kw.get('pd') else '',
				'form_no': kw.get('form_no') if kw.get('form_no') else 0,
				'requirements' : kw.get('requirements') if kw.get('requirements') else '',
				"user_id" : request.env.uid,
				"partner_id" : partner_id.id,

			})

		return request.render('rx_eyewear.opptician_detail_page_template', {'optic_product_ids': optic_product_ids})


