# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class Postal(models.Model):
	_name = 'postal.postal'
	_description = "Postal"
	_rec_name = "postal_district"

	postal_district = fields.Char(string="Postal District")
	# postal_code_ids = fields.One2many('postal.code','postal_code_id',string="Postal Sector")
	postal_code_ids = fields.Many2many('postal.code',string="Postal Sector")

class PostalCode(models.Model):
	_name = 'postal.code'
	_description = "Postal Code"
	_rec_name = "code"

	code = fields.Char(string="Code",size=6)
	postal_code_id = fields.Many2one('postal.postal')
