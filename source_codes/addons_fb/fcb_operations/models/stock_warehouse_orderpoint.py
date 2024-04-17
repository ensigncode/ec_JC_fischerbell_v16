# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import datetime, timedelta, date
from odoo.exceptions import UserError, ValidationError


class StockWarehouseOrderpoint(models.Model):
	_inherit = "stock.warehouse.orderpoint"

	def onchange_product_min_qty(self) :
		if self.product_id.use_expiration_date and self.product_id.tracking in ['serial','lot'] : 
			context = {}
			stock_move_ids = self.env['stock.move'].sudo().search([('product_id','=',self.product_id.id),('state','=','done')])
			if stock_move_ids:
				all_move_line_ids = [move_line for stock_move in stock_move_ids for move_line in stock_move.move_line_ids]
				sorted_move_line_ids = sorted(all_move_line_ids, key=lambda move_line: move_line.expiration_date or '')
				first_warehouse_id = sorted_move_line_ids[0].location_dest_id.warehouse_id if sorted_move_line_ids else False
				group_id = self.env.ref('stock.group_stock_manager')
				users = self.env['res.users'].search([('groups_id', 'in', [group_id.id])])
				email_addresses = users.mapped('email')
				email_to = ','.join(email_addresses)
				email_values = {
					'email_from': self.env.user.email_formatted,
					'email_cc': False,
					'email_to' : email_to,
					'auto_delete': False,
					
				}
				context.update({
					'warehouse_id' : first_warehouse_id.name if first_warehouse_id else False,
				})
				template = self.env.ref('fcb_operations.email_template_replenish_product_reminder')
				try:
					template.with_context(**context).send_mail(self._origin.id,force_send=True, raise_exception=False, email_values=email_values)
				except Exception as e:
					# Handle the exception gracefully
					raise UserError(_("Error : %s") % e)


	@api.model
	def create(self,vals) :
		res = super(StockWarehouseOrderpoint, self).create(vals)
		if 'product_min_qty' in vals and vals.get('product_min_qty') :
			res.onchange_product_min_qty()
		return res

	
	def write(self,vals) :
		res = super(StockWarehouseOrderpoint, self).write(vals)
		if 'product_min_qty' in vals and vals.get('product_min_qty') :
			self.onchange_product_min_qty()
		return res
