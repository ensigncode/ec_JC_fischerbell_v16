# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ResPartner(models.Model):
	_inherit = 'res.partner'

	postal_id = fields.Many2one('postal.postal',string="Postal District")
	postal_ids = fields.Many2many('postal.postal',string="Postal Districts")
	postal_code_ids = fields.Many2many('postal.code',readonly=False)
	is_driver = fields.Boolean(string="Is Driver")
	fleet_vehicle_ids = fields.One2many('fleet.vehicle','driver_id',string="Vehicle")

	def cron_onchange_postal_codes(self):
		partner_ids = self.search([])
		for partner in partner_ids :
			partner.onchange_postal_code_ids()
		
	@api.onchange('postal_ids')
	def onchange_postal_code_ids(self):
		for res in self:
			if res.postal_ids :
				res.write({
					'postal_code_ids': [(6, 0, res.postal_ids.postal_code_ids.ids)]
				})