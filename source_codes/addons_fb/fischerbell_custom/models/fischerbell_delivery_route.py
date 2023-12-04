# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api,fields, models
from odoo.exceptions import UserError, ValidationError

class FischerbellDeliveryRoute(models.Model):
	_name = 'fischerbell.delivery.route'
	_description = 'Delivery Route'

	name = fields.Char('Route')
	zone_line_ids = fields.One2many('fischerbell.delivery.route.line','route_id')


class FischerbellDeliveryRouteLine(models.Model):
	_name = 'fischerbell.delivery.route.line'
	_description = 'Fischerbell Delivery Zone Line'

	name = fields.Char('Postal Code')
	route_id = fields.Many2one('fischerbell.delivery.route', 'Parent')
