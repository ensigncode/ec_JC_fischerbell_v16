# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models,_
from odoo.exceptions import UserError


class StockPicking(models.Model):
	_inherit = "stock.picking"

	task_id = fields.Many2one('project.task', string="Task")
	attachment_ids = fields.Many2many(
		'ir.attachment','stock_attachment_rel', string='Attachments')
	pick_up = fields.Selection([
		('pc_driver', "Pickup by Driver"),
		('pc_supplier', "Pickup by Supplier"),
	], )

	def write(self, vals):
		result = super(StockPicking, self).write(vals)
		activity_model = self.env['mail.activity']
		activity_type = self.env.ref('mail.mail_activity_data_todo')

		for record in self:
			location_dest = vals.get('location_dest_id', record.location_dest_id.id)
			if self.env['stock.location'].browse(location_dest).name == 'Inspection' and record.state == 'assigned':
				existing_activity = self.env['mail.activity'].search([
					('res_id', '=', record.id),
					('activity_type_id', '=', activity_type.id),
					('summary', '=', 'Inspection Required')
				], limit=1)

				if not existing_activity:
					activity = activity_model.create({
						'res_id': record.id,
						'res_model_id': self.env.ref('stock.model_stock_picking').id,
						'activity_type_id': activity_type.id,
						'summary': 'Inspection Required',
						'note': 'Please inspect the items in this picking.',
						'date_deadline': fields.Date.today(),
						'user_id': record.env.user.id,
					})
					record.activity_ids = [(4, activity.id)]

		return result

	def button_validate(self):
		res = super().button_validate()
		for picking in self:
			pay_or_not = picking.sale_id.invoice_ids.sudo().search(
				[('payment_state', 'not in', ['paid', 'in_payment'])])
			if (picking.partner_id.l10n_in_gst_treatment == 'overseas' and
					pay_or_not.filtered(lambda x: x.sale_id == picking.sale_id) and
					not picking.sale_id.have_special_permission):
				raise UserError(_(
					" Before going to validate transfer, accounts must register payment for the %s."
				) % picking.sale_id.name)
				line_ids = picking.move_line_ids.filtered(lambda x: x.product_id.is_serviceable)
				for line in line_ids:
					if line.product_id.service_product_ids:
						eq_sale_id = line.picking_id.sale_id
						equipment_ids = self.env['equipment.service'].search(
							[('so_ref', '=', eq_sale_id.name), ('product_id', '=', line.product_id.id)])
						for eq_service in equipment_ids:
							eq_service.update({
								'serial_number': line.lot_id.name,
								'manufacturing_date': line.lot_id.manufacturing_date or False,
								'expire_date': line.lot_id.expiration_date or False
							})

		return res


