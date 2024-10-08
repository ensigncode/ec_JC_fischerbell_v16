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
	partner_seq = fields.Char('Customer Code', copy=False, default=lambda self: _('New'))
	e_invoice_email = fields.Char("E-Invoice Email")
	soa_email = fields.Char("Soa Email")

	no_delivery_days_selection = fields.Selection([('days', 'Days'), ('date', 'By Date')], string="Delivery Restriction")
	no_delivery_days = fields.Selection([
		('0', 'Monday'),
		('1', 'Tuesday'),
		('2', 'Wednesday'),
		('3', 'Thursday'),
		('4', 'Friday'),
		('5', 'Saturday'),
		('6', 'Sunday')], string="Delivery Restriction")
	delivery_restriction_start_date = fields.Date(string="Delivery Restriction Start")
	delivery_restriction_end_date = fields.Date(string="Delivery Restriction End")
	district_code = fields.Char(string='District Code', compute='_compute_distrct_code', store=True)
	code = fields.Char(string = 'Sequence', readonly=True, tracking=True)
	is_contact_created = fields.Boolean(string = 'Is Contact Created')
	currency_id = fields.Many2one('res.currency', readonly=False, store=True,
		string="Currency")
	pricelist_approval_state = fields.Selection([('pending','Pending'),('approved','Approved'),
										('rejected','Rejected')
										], string="Pricelist Approval", 
										tracking=True, copy=False)
	is_request_pricelist = fields.Boolean('Is Requested Pricelist')
	requested_pricelist_id = fields.Many2one('product.pricelist',string="Request PriceList")

	paymentterm_approval_state = fields.Selection([('pending','Pending'),('approved','Approved'),
										('rejected','Rejected')
										], string="Payment Term Approval", 
										tracking=True, copy=False)
	is_request_paymentterm = fields.Boolean('Is Requested Payment-Term')
	requested_payment_term_id = fields.Many2one('account.payment.term',string="Request Payment Term")


	creditlimit_approval_state = fields.Selection([('pending','Pending'),('approved','Approved'),
										('rejected','Rejected')
										], string="Credit Limit Approval", 
										tracking=True, copy=False)
	is_request_creditlimit = fields.Boolean('Is Requested Credit Limit')
	requested_credit_limit = fields.Float(string="Request Credit Limt")




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
	
	@api.depends('zip')
	def _compute_distrct_code(self):
		for rec in self:
			if rec.zip:
				district_code = self.env['postal.postal'].search([('postal_code_ids.code','in',[rec.zip[:2]])])
				rec.write({'district_code':district_code and district_code.postal_district or ''})
	
	def unlink(self):
		for rec in self:
			partner_id = rec.search([('name','=',rec.name),('email','=',rec.email),
									('phone','=',rec.phone),('mobile','=',rec.mobile),
									('is_contact_created','=',True)])
			if partner_id:
				partner_id.write({'is_contact_created':False})
		return super().unlink()

	def approve_creditlimt(self):
		for partner in self:
			partner.write({'credit_limit':partner.requested_credit_limit,
				'creditlimit_approval_state':'approved',
				'is_request_creditlimit':False,})

	def reject_creditlimt(self):
		for partner in self:
			partner.write({'is_request_creditlimit':False,
				'creditlimit_approval_state':'rejected'})

	def approve_pricelist(self):
		for partner in self:
			partner.write({'property_product_pricelist':partner.requested_pricelist_id,
				'pricelist_approval_state':'approved',
				'is_request_pricelist':False})

	def reject_pricelist(self):
		for partner in self:
			partner.write({'is_request_pricelist':False,
				'pricelist_approval_state':'rejected'})

	def approve_paymnetterm(self):
		for partner in self:
			partner.write({'property_payment_term_id':partner.requested_payment_term_id,
				'paymentterm_approval_state':'approved',
				'is_request_paymentterm':False,})

	def reject_paymnetterm(self):
		for partner in self:
			partner.write({'is_request_paymentterm':False,
				'paymentterm_approval_state':'rejected'})

	@api.model
	def create(self, vals):
		res = super(Partner, self).create(vals)
		if res.supplier_rank > 0:
			print('suppert_Rank')
			res['property_payment_term_id'] = self.env.ref('account.account_payment_term_30days').id
		if res.customer_rank > 0:
			res['property_payment_term_id'] = self.env.ref('account.account_payment_term_immediate').id
		return res
