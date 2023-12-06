# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api,fields, models

class Partner(models.Model):
	_inherit = "res.partner"

	attn_to = fields.Char('Attn To')
	type = fields.Selection(selection_add=[('followup', 'Pickup Address'),('dept_staff','Department Staff')], copy=True)
	batch_number = fields.Char('Batch Number')
	customer_code = fields.Char('Customer Code')
	fax = fields.Char('Fax')
	# customer_sku = fields.Char('Customer SKU')
	supplier_code = fields.Char('Supplier Code')
	currency_type = fields.Selection([
		('local', 'Local'),
		('overseas', 'Overseas'),
		('no',' ')
	], string='Currency Type')
	dept_code = fields.Char('Dept Code')
	product_tmpl_id = fields.Many2one('product.template', 'Product Template')
	user_training_ids = fields.One2many('fischerbell.user.training', 'partner_id', string="User Training")


	@api.onchange('property_purchase_currency_id')
	def _onchange_currency_type(self):
		self.currency_type = 'no'
		company = self.env['res.company'].search([], limit=1)
		if self.property_purchase_currency_id and company and self.property_purchase_currency_id == company.currency_id:
			self.currency_type = 'local'
		elif self.property_purchase_currency_id and company and self.property_purchase_currency_id != company.currency_id:
			self.currency_type = 'overseas'
		else:
			self.currency_type = 'no'