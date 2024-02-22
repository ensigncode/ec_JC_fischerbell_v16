# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ResPartner(models.Model):
	_inherit = 'res.partner'

	postal_id = fields.Many2one('postal.postal',string="Postal District")
	postal_code_ids = fields.Many2many(related="postal_id.postal_code_ids",readonly=False)
	is_driver = fields.Boolean(string="Is Driver")
	fleet_vehicle_ids = fields.One2many('fleet.vehicle','driver_id',string="Vehicle")
	