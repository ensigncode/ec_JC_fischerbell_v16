# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, models, tools, _, fields


class FitTestTraining(models.Model):
	_name = "fit.test.training"
	_description = "Website Fit Test Training"

	name = fields.Char('Name of Trainer')
	charge_name = fields.Char('Person In-charge ')
	date = fields.Date('Date of Training')
	phone = fields.Char('Contact No.')
	company = fields.Char('Name Of Company')
	training_type = fields.Char('Type of Training')
	number_of_person = fields.Integer(string='Number Of Person', default=1)
	location = fields.Char(string='Locations')
	fit_ids = fields.One2many('fit.trainee', 'fit_id', string="Fit Lines")


class FitTestTrainingTrainee(models.Model):
	_name = "fit.trainee"
	_description = "Fit Test Trainee"

	trainee = fields.Char(string="Trainee")
	passport_no = fields.Char(string="NRIC / Passport NO./ Employee No.")
	size = fields.Integer(string="Size")
	is_pass_fail = fields.Boolean(string="Pass / Fail")
	tested_on = fields.Date(string="Tested On")
	fit_id = fields.Many2one('fit.test.training', string="Fit")



