# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError

class SkipReasonLline(models.Model):
	_name = 'skip.reason.line'

	name = fields.Char('Reason')
	reason_date = fields.Datetime('Reason Date')
	picking_id = fields.Many2one('stock.picking',string="Picking")

class StockPicking(models.Model):
	_inherit = 'stock.picking'

	skip_reason_line_ids = fields.One2many('skip.reason.line','picking_id',string="Skip Reasons")
	successfull_delivery = fields.Boolean(string="Successfull Delivery",default=True)
	responsible_customer_id = fields.Many2one('res.partner',string="Responsible customer")
	latest_skip_reason = fields.Char(string="Latest Skip Reason", compute="_compute_latest_skip_reason")
	
	def _compute_latest_skip_reason(self):
		for picking in self:
			latest_skip_reason = picking.skip_reason_line_ids.sorted('create_date', reverse=True)[:1].name
			picking.latest_skip_reason = latest_skip_reason
	
	def send_notification_skip_delivery(self,reason_value=None):
		self = self.sudo()
		context = {'reason_value' : reason_value}
		email_values = {
			'email_from': self.env.user.email_formatted,
			'email_cc': False,
			'auto_delete': False,
		}
		template = self.env.ref('portal_signature.email_template_skip_delivery_notification')
		if self.picking_type_code == 'outgoing' :
			sale_manager_group_id = self.env.ref('sales_team.group_sale_manager')
			sale_managers = self.env['res.users'].search([('groups_id', 'in', sale_manager_group_id.ids)])
			email_addresses = sale_managers.mapped('email')
			email_to = ','.join(email_addresses)
			email_values.update({
				'email_to' : email_to,
			})
			try:
				template.with_context(**context).send_mail(self.id,force_send=True, raise_exception=False, email_values=email_values)
			except Exception as e:
				# Handle the exception gracefully
				raise UserError(_("Error : %s") % e)

		if self.picking_type_code == 'incoming' :
			purchase_manager_group_id = self.env.ref('purchase.group_purchase_manager')
			purchase_managers = self.env['res.users'].search([('groups_id', 'in', purchase_manager_group_id.ids)])
			email_addresses = purchase_managers.mapped('email')
			email_to = ','.join(email_addresses)
			email_values.update({
				'email_to' : email_to,
			})
			try:
				template.with_context(**context).send_mail(self.id,force_send=True, raise_exception=False, email_values=email_values)
			except Exception as e:
				# Handle the exception gracefully
				raise UserError(_("Error : %s") % e)
		self.next_delivery_date = (fields.Datetime.today() + relativedelta(days=1))
		self.successfull_delivery = False
		reason_line = self.skip_reason_line_ids.create({
            'name': reason_value,
            'reason_date': fields.Datetime.now(),
            'picking_id': self.id,
        })
		return True

