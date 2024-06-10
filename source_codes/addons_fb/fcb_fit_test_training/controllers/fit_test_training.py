# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http
from odoo.http import request
import json


class FitTestTrainingController(http.Controller):
	@http.route(['/fittest_training'], type='http', auth='public', website=True)
	def fittest_training_page_method(self, **kw):
		return request.render('fcb_fit_test_training.tmp_fittest_training_page_form', {})


	@http.route(['/fittest_training/submit'], type='http', auth="public", website=True)
	def fittest_training_form_submit(self, **kw):
		trainer_id = request.env['fit.test.training'].sudo().search(
			[('reference_no', 'like', kw.get('reference_no'))])
		if trainer_id:
			val = [(0, 0, line) for line in json.loads(kw.get('fit_ids'))] if kw.get('fit_ids') else False
			trainer_id = trainer_id.sudo().write({'fit_ids': val}) if val else False
		else:
			return request.render('fcb_fit_test_training.tmp_fittest_training_page_form', {})

		return request.render("fcb_fit_test_training.tmp_fittest_training_form_success",
							  {'trainer_id': trainer_id} if trainer_id else {})


