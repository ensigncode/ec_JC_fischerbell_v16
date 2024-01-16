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

