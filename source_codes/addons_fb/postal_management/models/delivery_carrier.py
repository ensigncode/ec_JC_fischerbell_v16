# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class DeliveryCarrier(models.Model):
	_inherit = 'delivery.carrier'
	
	assigned_driver = fields.Many2one('res.partner',string="Assigned Driver")

