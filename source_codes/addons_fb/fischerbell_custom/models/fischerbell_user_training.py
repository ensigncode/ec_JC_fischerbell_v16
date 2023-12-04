# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api,fields, models
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date

class FischerbellUserTraining(models.Model):
	_name = 'fischerbell.user.training'
	_description = 'Fischerbell User Training'

	name = fields.Char('Trainer Name')
	datetime = fields.Datetime('Trainer Date amd Time')
	venue = fields.Char('Trainer Venue')
	type = fields.Char('Type of Training')
	partner_id = fields.Many2one('res.partner')




