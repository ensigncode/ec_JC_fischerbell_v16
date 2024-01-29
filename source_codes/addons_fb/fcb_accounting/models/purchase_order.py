# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError

class PurchaseOrder(models.Model):
	_inherit = 'purchase.order'

	
	def _create_picking(self):
		StockPicking = self.env['stock.picking']
		for order in self.filtered(lambda po: po.state in ('purchase', 'done')):
			if any(product.type in ['product', 'consu'] for product in order.order_line.product_id):
				order = order.with_company(order.company_id)
				picking_type_ids = order.order_line.picking_type_id
				for picking_type_id in picking_type_ids:
					pickings = order.picking_ids.filtered(lambda x: x.state not in ('done', 'cancel') and x.picking_type_id.id == picking_type_id.id)
					if not pickings:
						res = order.with_context(picking_type_id=picking_type_id)._prepare_picking()
						picking = StockPicking.with_user(SUPERUSER_ID).create(res)
						pickings = picking
					else:
						picking = pickings[0]
					order_lines = order.order_line.filtered(lambda x:x.picking_type_id.id == picking_type_id.id)
					if order_lines:
						moves = order_lines._create_stock_moves(picking)
						moves = moves.filtered(lambda x: x.state not in ('done', 'cancel'))._action_confirm()
						seq = 0
						for move in sorted(moves, key=lambda move: move.date):
							seq += 5
							move.sequence = seq
						moves._action_assign()
						# Get following pickings (created by push rules) to confirm them as well.
						forward_pickings = self.env['stock.picking']._get_impacted_pickings(moves)
						(pickings | forward_pickings).action_confirm()
						picking.message_post_with_view('mail.message_origin_link',
							values={'self': picking, 'origin': order},
							subtype_id=self.env.ref('mail.mt_note').id)
		return True


	def _get_destination_location(self):
		self.ensure_one()
		# if self.dest_address_id:
		# 	return self.dest_address_id.property_stock_customer.id

		if 'picking_type_id' in self._context and self._context['picking_type_id']:
			picking_type_id = self._context['picking_type_id']
		else:
			picking_type_id = self.picking_type_id
		return picking_type_id.default_location_dest_id.id

	def _prepare_picking(self):
		if not self.group_id:
			self.group_id = self.group_id.create({
				'name': self.name,
				'partner_id': self.partner_id.id
			})
		if not self.partner_id.property_stock_supplier.id:
			raise UserError(_("You must set a Vendor Location for this partner %s", self.partner_id.name))
		if 'picking_type_id' in self._context and self._context['picking_type_id']:
			picking_type_id = self._context['picking_type_id']
		else:
			picking_type_id = self.picking_type_id
		return {
			'picking_type_id': picking_type_id.id,
			'partner_id': self.partner_id.id,
			'user_id': False,
			'date': self.date_order,
			'origin': self.name,
			'location_dest_id': self.with_context(picking_type_id=picking_type_id)._get_destination_location(),
			'location_id': self.partner_id.property_stock_supplier.id,
			'company_id': self.company_id.id,
		}

class PurchaseOrderLine(models.Model):
	_inherit = 'purchase.order.line'

	@api.model
	def _default_picking_type(self):
		return self.order_id.picking_type_id

	picking_type_id = fields.Many2one('stock.picking.type',
			'Deliver To',
			required=True, default=_default_picking_type,
			help="This will determine operation type of incoming shipment")
