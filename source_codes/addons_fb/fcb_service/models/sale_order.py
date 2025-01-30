# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from datetime import timedelta
from odoo.exceptions import UserError, ValidationError



class SaleOrder(models.Model):
	_inherit = "sale.order"

	service_product_ids = fields.One2many('product.service', 'sale_product_tmp_id', 'Service Products')
	have_special_permission = fields.Boolean("Internal Remarks")
	have_special_permission_note = fields.Text(string='Description', required=False)
	equipment_service_id = fields.Many2one('equipment.service', string='Equipment Service')

	def _get_invoiceable_lines(self, final=False):
		""" Override to include all lines for prepayment logic. """
		if self.have_special_permission:
			return self.order_line.filtered(lambda l: not l.display_type)
		return super(SaleOrder, self)._get_invoiceable_lines(final=final)
		
	@api.onchange('have_special_permission')
	def onchange_have_special_permission(self) :
		for order in self:
			if order.have_special_permission :
				prepayment_term = self.env.ref('fcb_service.account_payment_term_prepayment', raise_if_not_found=False)
				if not prepayment_term:
					raise ValidationError(_("Prepayment payment term is not configured. Please contact the administrator."))
				order.payment_term_id = prepayment_term
				self.invoice_status = 'to invoice'
			else:
				order.payment_term_id = order.partner_id.property_payment_term_id.id
				self.invoice_status = 'no'

	def _check_prepayment_done(self):
		""" Check if the required prepayment has been completed for this sale order. """
		self.ensure_one()
		prepayment_amount = sum(payment.amount for payment in self.invoice_ids.filtered(
			lambda inv: inv.state == 'posted' and inv.payment_state == 'paid'
		))
		if prepayment_amount < self.amount_total:
			return False
		return True

	def action_confirm(self):
		""" Override to check for prepayment and allow invoice creation. """
		if self.have_special_permission:
			prepayment_term = self.env.ref('fcb_service.account_payment_term_prepayment', raise_if_not_found=False)
			if not prepayment_term:
				raise ValidationError(_("Prepayment payment term is not configured. Please contact the administrator."))
			self.payment_term_id = prepayment_term
			self.invoice_status = 'to invoice'
			self.env.cr.commit()  # Persist the invoice_status

			# Raise validation error if prepayment is incomplete
			prepayment_done = sum(payment.amount_total for payment in self.invoice_ids.filtered(
				lambda inv: inv.state == 'posted' and inv.payment_state == 'paid'
			)) >= self.amount_total
			if not prepayment_done:
				raise ValidationError(_(
					"Prepayment is required before confirming this order.\n"
					"Please create and process the prepayment invoice before confirming."
				))
		return super(SaleOrder, self).action_confirm()
	
	@api.model_create_multi																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																		
	def create(self, vals_list):
		res = super().create(vals_list)
		for record in res:
			if record.order_line:
				for product_line in record.order_line:
					if product_line.product_id.service_product_ids:
						move_lines = []
						for service_product in product_line.product_id.service_product_ids:
							service_date = (record.date_order.date() + timedelta(
								days=service_product.service_time))
							reminder_date = service_date - timedelta(days=service_product.reminder_time)
							move_line = (0, 0, {
								'product_variant_id': product_line.product_id.id or False,
								'service_date': service_date,
								'reminder_date': reminder_date,
								'service_product_id':  service_product.product_variant_id.id,
							})
							move_lines.append(move_line)
						record.update({'service_product_ids': move_lines})
		return res

	def write(self,vals):
		res = super().write(vals)
		if 'have_special_permission' in vals:
			if self.have_special_permission:
				self.invoice_status = 'to invoice'
			else:
				self.invoice_status = 'no'




		return res

	def action_to_approve(self):
		res = super(SaleOrder, self).action_to_approve()
		# picking_ids = self.picking_ids.fillter
		# print('vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv',equipment_records)
		for record in self:
			if record.service_product_ids:
				for service in record.service_product_ids:
					equipment_service_vals = {
						'product_id': service.product_variant_id.id,
						'service_product_id': service.service_product_id.id,
						# 'serial_number': line.lot_id.name,
						'partner_id': self.partner_id.id,
						'so_ref': self.name,
						# 'manufacturing_date': line.lot_id.manufacturing_date,
						# 'expire_date': line.lot_id.expiration_date,
						'categ_id': service.product_variant_id.categ_id.id,
						'delivered_date': self.date_order,
						'eq_service_date': service.service_date,
						'eq_reminder_date': service.reminder_date,
					}
					self.env['equipment.service'].create(equipment_service_vals)
		return res
