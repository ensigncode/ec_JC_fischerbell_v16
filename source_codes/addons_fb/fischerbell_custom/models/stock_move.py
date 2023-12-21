# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api,fields, models
from odoo.exceptions import UserError, ValidationError

class StockMove(models.Model):
	_inherit = "stock.move"

	customer_id = fields.Many2one('res.partner', 'Customer Name')
	phone = fields.Char('Contact', related="customer_id.phone")
	batch_number = fields.Char('Batch Number', related="customer_id.batch_number")
	lot_id = fields.Many2one('stock.lot', 'Serial Number')
	mrp_line_id = fields.Many2one('stock.move', compute="_compute_mrp_line_id", store=True)
	mrp_customer_id = fields.Many2one('res.partner', compute="_compute_mrp_line_id", store=True)
	mrp_phone = fields.Char('Phone Number', compute="_compute_mrp_line_id", store=True)
	send_email_reorder = fields.Boolean('Send Email To Reorder', default=False)

	@api.onchange('customer_id')
	def onchange_batch_number(self):
		if self.customer_id:
			self.batch_number = self.customer_id.batch_number
		else:
			self.batch_number = False


	def confirm_stock(self):
		qty = int(self.product_uom_qty)
		for move_line in self.move_line_ids:
			if move_line.qty_done > self.product_uom_qty:
				raise ValidationError("Sorry, you cannot input the quantity more than "+str(qty))
			else:
				pass

		return True


	@api.depends('picking_id.operation_id.move_raw_ids.customer_id')
	def _compute_mrp_line_id(self):
		self.mrp_phone = False
		self.mrp_customer_id = False
		list_mrp_line = []
		for move in self:
			if move.picking_id.operation_id.move_raw_ids.customer_id:
				for mrp_line in move.picking_id.operation_id.move_raw_ids:
					list_mrp_line.append(mrp_line.id)

			if list_mrp_line:
				mrp_line_obj = self.env['stock.move'].search([('id','in',list_mrp_line)])
				if mrp_line_obj:
					for line in mrp_line_obj:
						move.mrp_line_id = line.id
						move.mrp_customer_id = line.customer_id.id
						move.mrp_phone = line.phone


class StockWarehouseOrderpoint(models.Model):
	_inherit = "stock.warehouse.orderpoint"

	qty_on_hand = fields.Float('On Hand', readonly=True, compute='_compute_qty', digits='Product Unit of Measure',store=False)

	def cron_min_qty_alert(self):
		self.action_send_email_for_min_qty()
		return True

	def action_send_email_for_min_qty(self):
		order = self.search([('send_email_reorder','=',False)]).filtered(lambda line: line.qty_on_hand and line.product_min_qty and line.qty_on_hand <= line.product_min_qty)
		order.write({'send_email_reorder' : True})
		reorder_orderpoint_products = '<br/>'.join([f"<li>Product : {orderpoint_id.product_id.name}, On Hand :{str(orderpoint_id.qty_on_hand)}, Min Qty : {str(orderpoint_id.product_min_qty)}</li>" for orderpoint_id in order])
		if reorder_orderpoint_products:
			body = f"""<p><b>Reminder To Reorder This Products</b></p><br/>{reorder_orderpoint_products}"""
			subject = (f""" Reminder To Reorder """)
			email_to_partner = self.env.ref('purchase.group_purchase_manager').users.partner_id
			mails = {
				'subject': subject,
				'email_from': self.env.user.email_formatted,
				'recipient_ids': email_to_partner.ids,
				'body_html': body,
				'auto_delete': True,
			}
			mail = self.env['mail.mail'].create(mails)
			mail.send()

	def action_replenish(self):
		for rec in self:
			rec.send_email_reorder = False
		return super(StockWarehouseOrderpoint, self).action_replenish()


