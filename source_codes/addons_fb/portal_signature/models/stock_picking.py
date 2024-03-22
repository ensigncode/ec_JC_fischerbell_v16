# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class StockPicking(models.Model):
	_inherit = 'stock.picking'
	
	def send_notification_skip_delivery(self,reason_val=None):
		self = self.sudo()
		if self.picking_type_code == 'outgoing' :
			sale_manager_group_id = self.env.ref('sales_team.group_sale_manager')
			sale_managers = self.env['res.users'].search([('groups_id', 'in', sale_manager_group_id.ids)])
			for manager in sale_managers:
				self.env['mail.message'].create({
					'partner_ids': [(4, manager.partner_id.id)],
					'subject': 'Skip Delivery Notification',
					'body': "This delivery" + self.name + " has been skipped due to the following reason: " + reason_val,
					'model': 'stock.picking',
					'res_id': self.id,
					'message_type' : 'notification',
				})
		if self.picking_type_code == 'incoming' :
			purchase_manager_group_id = self.env.ref('purchase.group_purchase_manager')
			purchase_managers = self.env['res.users'].search([('groups_id', 'in', purchase_manager_group_id.ids)])

			# Send system notification to all purchase managers
			for manager in purchase_managers:
				self.env['mail.message'].create({
					'partner_ids': [(4, manager.partner_id.id)],
					'subject': 'New Stock Picking Notification',
					'body': message,
					'model': 'stock.picking',
					'res_id': self.id,
					'message_type' : 'notification',
				})

