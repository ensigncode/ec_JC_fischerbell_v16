# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api,fields, models, _

class Partner(models.Model):
	_inherit = "res.partner"

	attn_to = fields.Char('Attn To')
	type = fields.Selection(selection_add=[('followup', 'Pickup Address'),('dept_staff','Department Staff')], copy=True)
	batch_number = fields.Char('Batch Number')
	customer_code = fields.Char('Customer Code', store=True)
	fax = fields.Char('Fax')
	# customer_sku = fields.Char('Customer SKU')
	supplier_code = fields.Char('Supplier Code')
	currency_type = fields.Selection([
		('local', 'Local'),
		('overseas', 'Overseas'),
		('no', 'No')
	], string='Currency Type')
	dept_code = fields.Char('Dept Code')
	product_tmpl_id = fields.Many2one('product.template', 'Product Template')
	user_training_ids = fields.One2many('fischerbell.user.training', 'partner_id', string="User Training")
	platform_name = fields.Char(string='Platform Name')
	platform_login = fields.Char(string='Login')
	platform_pwd = fields.Char(string='Password')
	delivery_instruction = fields.Html(string="Delivery Instruction")
	invoice_instruction = fields.Html(string="Invoice Instruction")
	credit_limit = fields.Float(string='Credit Limit')
	type_of_invoice = fields.Selection(selection=[('e_invoice', 'E-Invoice'), ('paper_invoice', 'Paper Invoice')],
	    string='Type Of Invoice', required=True)
	partner_seq = fields.Char('Sequence', copy=False, default=lambda self: _('New'))
	e_invoice_email = fields.Char("E-Invoice Email")
	soa_email = fields.Char("Soa Email")

	no_delivery_days_selection = fields.Selection([('days', 'Days'), ('date', 'By Date')], string="Delivery Restriction")
	no_delivery_days = fields.Selection([
		('0', 'Sunday'),
		('1', 'Monday'),
		('2', 'Tuesday'),
		('3', 'Wednesday'),
		('4', 'Thursday'),
		('5', 'Friday'),
		('6', 'Saturday')], string="Delivery Restriction")
	delivery_restriction_start_date = fields.Date(string="Delivery Restriction Start")
	delivery_restriction_end_date = fields.Date(string="Delivery Restriction End")



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

	@api.model
	def create(self, vals):
		if vals.get('parent_id'):
			parent_id = self.browse(vals.get('parent_id'))
			vals['customer_code'] = parent_id.customer_code
		res = super(Partner, self).create(vals)
		return res


	def write(self, vals):
		if vals.get('customer_code'):
			for customer in self.child_ids:
				customer.customer_code = vals.get('customer_code')
		res = super().write(vals)
		return res

