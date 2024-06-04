# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, models, tools, _, fields


class FitTestTraining(models.Model):
	_name = "fit.test.training"
	_description = "Website Fit Test Training"

	name = fields.Char('Name')
	name_of_trainer = fields.Many2one('res.partner','Name of Trainer')
	charge_name = fields.Char('Person In-charge ')
	date = fields.Date('Date of Training')
	phone = fields.Char('Contact No.')
	company = fields.Many2one('res.partner','Name Of Company')
	training_type = fields.Char('Type of Training')
	number_of_person = fields.Integer(string='Number Of Person', default=1)
	location = fields.Char(string='Locations')
	fit_ids = fields.One2many('fit.trainee', 'fit_id', string="Fit Lines")
	training_types = fields.Selection([('aed','Fit Test - AED'),
	                               ('scba','Fit Test - SCBA'),
	                               ('spill_traning','Fit Test - Spill Training'),
	                               ('fit_test','Fit Test')],default="fit_test")
	trainer_sign = fields.Binary(string="Trainer signature")
	partner_id = fields.Many2one('res.partner','Partner')

	def action_send_email(self):
		self.ensure_one()
		lang = self.env.context.get('lang')
		template_id = self.env.ref('fcb_fit_test_training.email_template_fit_test', raise_if_not_found=False)
		if template_id and template_id.lang:
			lang = template_id._render_lang(self.ids)[self.id]
		ctx = {
			'default_model': 'fit.test.training',
			'default_res_id': self.id,
			'default_use_template': bool(template_id),
			'default_template_id': template_id.id if template_id else None,
			'default_composition_mode': 'comment',
			'mark_so_as_sent': True,
			'default_email_layout_xmlid': 'mail.mail_notification_layout_with_responsible_signature',
			'proforma': self.env.context.get('proforma', False),
			'force_email': True,
			'model_description': self.with_context(lang=lang).name,
		}
		return {
			'type': 'ir.actions.act_window',
			'view_mode': 'form',
			'res_model': 'mail.compose.message',
			'views': [(False, 'form')],
			'view_id': False,
			'target': 'new',
			'context': ctx,
		}

class FitTestTrainingTrainee(models.Model):
	_name = "fit.trainee"
	_description = "Fit Test Trainee"

	trainee = fields.Char(string="Trainee")
	passport_no = fields.Char(string="NRIC / FIN NO./ Employee No.")
	size = fields.Char(string="Size")
	is_pass_fail = fields.Boolean(string="Pass / Fail")
	tested_on = fields.Date(string="Tested On")
	fit_id = fields.Many2one('fit.test.training', string="Fit")



