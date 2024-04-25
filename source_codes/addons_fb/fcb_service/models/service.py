# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models,_


class Task(models.Model):
	_inherit = "project.task"

	count_transfer = fields.Integer(string='Transfers', compute='_compute_count_transfer')

	def _compute_count_transfer(self):
		for picking in self:
			count = self.env['stock.picking'].search_count([('task_id', '=', picking.id)])
			picking.count_transfer = count

	def send_for_inspection(self):
		stage_id = self.env['helpdesk.stage'].search([('name', '=', 'Inspection pending')], limit=1)
		if stage_id:
			self._update_stage(stage_id)
			repair_location = self.env.ref('fcb_service.location_repair')  # Replace 'module_name' with your module name
			inspection_location = self.env.ref('fcb_service.location_inspection')
			self._create_picking(repair_location, inspection_location, 'internal', 'Inspection', state='confirmed')
			inspection_location = self.env.ref('fcb_service.location_inspection')
			output_location = self.env.ref('stock.stock_location_output')
			self._create_picking(inspection_location, output_location, 'internal', 'PUT TO OUT', state='assigned')

	def _update_stage(self, stage_id):
		self.stage_id = stage_id.id

	def _create_picking(self, src_location, dest_location, location_usage, picking_name, state=None):
		picking_type = self.env['stock.picking.type'].search([('code', '=', 'internal'), ('name', '=', picking_name)],
		                                                     limit=1)

		move_lines = []
		vals = {
			'partner_id': self.partner_id.id,
			'location_id': src_location.id,
			'location_dest_id': dest_location.id,
			'picking_type_id': picking_type.id,
			'origin': self.name,
			'task_id': self.id,
		}
		move_line = (0, 0, {
			'product_id': self.product_id.id or False,
			'name': self.product_id.name,
			'product_uom_qty': 1,
			'location_id': src_location.id,
			'location_dest_id': dest_location.id,
		})
		move_lines.append(move_line)
		vals.update({'move_ids_without_package': move_lines})
		picking_obj = self.env['stock.picking'].create(vals)
		picking_obj.action_confirm()

		# Update the state of the picking based on the provided state parameter
		# if state:
		#     picking_obj.state = state

		return picking_obj

	def done_inspection(self):
		stage_id = self.env['helpdesk.stage'].search([('name', '=', 'Done')], limit=1)
		self.stage_id = stage_id.id

	def show_transfer(self):
		self.ensure_one()
		return {
			'name': _('Transfer all'),
			'view_mode': 'tree,form',
			'res_model': 'stock.picking',
			'type': 'ir.actions.act_window',
			'domain': [('task_id', '=', self.id)],
			'target': 'current',
		}
