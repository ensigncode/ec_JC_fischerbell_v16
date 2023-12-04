# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api,fields, models
from odoo.exceptions import UserError, ValidationError
import psycopg2.extensions

class AccountMoveLine(models.Model):
	_inherit = "account.move.line"

	sale_ids = fields.Many2many('sale.order', 'sale_bill_line_rel', 'sale_id', 'bill_line_id', string="Sales Order")
	picking_ids = fields.Many2many('stock.picking', 'picking_bill_line_rel', 'picking_id', 'bill_line_id', string="Delivery Order")
	move_ids = fields.Many2many('account.move', 'inv_bill_line_rel', 'move_id', 'bill_line_id', string="Invoices")

	# def _compute_sale_ids(self):
	# 	self.ensure_one()
	# 	list_sales = []
	# 	self.sale_ids = False
	# 	self.move_ids = False
	# 	self.picking_ids = False
	# 	for line in self:
	# 		if line.purchase_line_id:
	# 			line.sale_ids = line.purchase_line_id.sale_line_id.order_id
	# 			sales = self.env['sale.order'].search([('id','=',line.purchase_line_id.sale_line_id.order_id.id),('state','!=','cancel')], limit=1)
	# 			if sales:
	# 				pickings = sales.picking_ids.filtered(lambda x: x.state !='cancel' and x.picking_type_code == 'outgoing')
	# 				if pickings:
	# 					line.picking_ids = pickings
	# 				else:
	# 					line.picking_ids = False


	# 				moves = sales.invoice_ids.filtered(lambda x: x.state !='cancel')
	# 				if moves:
	# 					line.move_ids = moves
	# 				else:
	# 					line.move_ids = False
	# 			else:
	# 				line.move_ids = False
	# 		else:
	# 			line.move_ids = False
				

	def _create_analytic_lines(self):
		""" Create analytic items upon validation of an account.move.line having an analytic distribution.
		"""
		# self._validate_analytic_distribution()
		analytic_line_vals = []
		for line in self:
			analytic_line_vals.extend(line._prepare_analytic_lines())

		self.env['account.analytic.line'].create(analytic_line_vals)

