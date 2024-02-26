# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ResPartner(models.Model):
	_inherit = 'res.partner'

	postal_id = fields.Many2one('postal.postal',string="Postal District")
	postal_ids = fields.Many2many('postal.postal',string="Postal Districts")
	postal_code_ids = fields.Many2many('postal.code',compute="compute_postal_code_ids",readonly=False)
	is_driver = fields.Boolean(string="Is Driver")
	fleet_vehicle_ids = fields.One2many('fleet.vehicle','driver_id',string="Vehicle")

	def compute_postal_code_ids(self):
		for res in self:
			if res.postal_ids :
				res.write({
					'postal_code_ids': [(4, postal.id) for postal in res.postal_ids.postal_code_ids]
				})
	