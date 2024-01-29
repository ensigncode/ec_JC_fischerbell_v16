# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http
from odoo.http import request


class FitTestTrainingController(http.Controller):
	@http.route(['/fittest_training'], type='http', auth='public', website=True)
	def fittest_training_page_method(self, **kw):
		return request.render('fcb_fit_test_training.tmp_fittest_training_page_form', {})

	@http.route(['/fittest_training/submit'], type='http', auth="public", website=True)
	def fittest_training_form_submit(self, **kw):
		trainer_id = request.env['fit.test.training'].sudo().create({
			'name': kw.get('name'),
			'date': kw.get('date'),
			'charge_name': kw.get('charge_name'),
			'training_type': kw.get('training_type'),
			'company': kw.get('company'),
			'phone': kw.get('phone'),
			'number_of_person': kw.get('number_of_person'),
			'location': kw.get('location'),
		})
		vals = {
			'trainer_id': trainer_id
		}
		return request.render("fcb_fit_test_training.tmp_fittest_training_form_success", vals)


