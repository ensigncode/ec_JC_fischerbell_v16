# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api,fields, models
from odoo.exceptions import UserError, ValidationError

class FischerbellDeliveryRoute(models.Model):
	_name = 'fischerbell.delivery.route'
	_description = 'Delivery Route'

	name = fields.Char('Route')
	zone_line_ids = fields.One2many('fischerbell.delivery.route.line','route_id')


	def name_get(self):
		if self._context.get('picking_id'):
			partner_shipping_id = self.env['stock.picking'].browse(self._context.get('picking_id')[0])
			partner_zip = '{:.2}'.format(partner_shipping_id.partner_id.zip)
			result = []
			for rec in self:
				result.append((rec.id, '%s - %s' % (rec.name, partner_zip)))
			return result
		else:
			return super().name_get()



class FischerbellDeliveryRouteLine(models.Model):
	_name = 'fischerbell.delivery.route.line'
	_description = 'Fischerbell Delivery Zone Line'

	name = fields.Char('Postal Code')
	route_id = fields.Many2one('fischerbell.delivery.route', 'Parent')
