# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from operator import attrgetter
from re import findall as regex_findall, split as regex_split

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class StockLot(models.Model):
	_inherit = 'stock.lot'

	tracking = fields.Selection([
		('serial', 'By Unique Serial Number'),
		('lot', 'By Batch'),
		('none', 'No Tracking')],
		string="Tracking", required=True, default='none',
		compute='_compute_get_tracking', store=True)
	attribute_one = fields.Html('Attribute 1')
	attribute_two = fields.Html('Attribute 2')

	@api.depends('product_id.tracking')
	def _compute_get_tracking(self):
		self.tracking = 'none'
		for stock_lot in self:
			if stock_lot.product_id.tracking:
				stock_lot.tracking = stock_lot.product_id.tracking
			else:
				stock_lot.tracking = 'none'
