# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api,fields, models
from odoo.exceptions import UserError, ValidationError

class FischerbellConfigurationNote(models.Model):
	_name = 'fischerbell.configuration.note'
	_description = 'Fischerbell Configuration Note'

	name = fields.Char('Name')
	partner_ids = fields.Many2many('res.partner', 'config_note_partner_rel', 'config_note_id', 'partner_id', string="Contact")
	note = fields.Text('Note')
	type = fields.Selection([
		('sale', 'Sales'),
		('purchase', 'Purchase'),
		('account', 'Accounting'),
		('picking', 'Inventory'),
		('manufacture', 'Manufacture')
	], string="Module")
