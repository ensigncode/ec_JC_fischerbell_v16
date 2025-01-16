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
	manufacturing_date = fields.Date('manufacturing date',compute='_compute_get_manufacturing_date')
	is_from_po = fields.Boolean('IS From PO')
	is_from_service = fields.Boolean('IS From Services')

	@api.depends('product_id.tracking')
	def _compute_get_tracking(self):
		self.tracking = 'none'
		for stock_lot in self:
			if stock_lot.product_id.tracking:
				stock_lot.tracking = stock_lot.product_id.tracking
			else:
				stock_lot.tracking = 'none'
				

	@api.depends('manufacturing_date')
	def _compute_get_manufacturing_date(self):
		for record in self:
			move_line = self.env['stock.move.line'].search([('lot_id', '=', record.id)], limit=1)
			if move_line:
				record.manufacturing_date = move_line.manufacturing_date
			else:
				record.manufacturing_date = False
				

class StockLocation(models.Model):
	_inherit = 'stock.location'


	inventory_status = fields.Boolean('Show in Inventory Status')

