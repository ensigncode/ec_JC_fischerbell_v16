# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http
from odoo.http import request


class FitTestTrainingController(http.Controller):
	@http.route(['/fittest_training'], type='http', auth='public', website=True)
	def fittest_training_page_method(self, **kw):
		return request.render('fcb_fit_test_training.tmp_fittest_training_page_form', {})

	@http.route(['/fittest_training/submit'], type='http', auth="public", website=True)
	def fittest_training_form_submit(self, **kw):
		partner_id = int(kw.get('partner_id', False)) if kw.get('partner_id') else False
		company_id = int(kw.get('company_id', False)) if kw.get('company_id') else False
		trainer_id = request.env['fit.test.training'].sudo().create({
			'name': kw.get('name'),
			'name_of_trainer': request.env['res.partner'].sudo().browse(partner_id).id,
			'date': kw.get('date'),
			'charge_name': kw.get('charge_name'),
			'training_type': kw.get('training_type'),
			'company': request.env['res.partner'].sudo().browse(company_id).id,
			'phone': kw.get('phone'),
			# 'number_of_person': kw.get('number_of_person'),
			'location': kw.get('location'),
			'fit_ids' : [(0, 0, {
                    'trainee': kw.get('trainee_name'),
					'passport_no': kw.get('passport_no'),
                })]
		})
		vals = {
			'trainer_id': trainer_id
		}
		return request.render("fcb_fit_test_training.tmp_fittest_training_form_success", vals)


