# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date
from odoo.tools.float_utils import float_round
import qrcode
import io
import base64
from werkzeug.urls import url_parse


class ProductTemplate(models.Model):
	_inherit = "product.template"

	max_price = fields.Float('Max Sales Price')
	min_price = fields.Float('Min Sales Price')
	sales_line_ids = fields.One2many('sale.order.line', 'product_template_id', 'Sales Line')
	sale_lines_ids = fields.Many2many('sale.order.line','Sale Lines', compute ='_compute_lines')
	purchase_line_ids = fields.One2many('purchase.order.line', 'product_template_id', 'Purchase Line Id')
	purchase_lines_ids = fields.Many2many('purchase.order.line','Purchase Lines', compute ='_compute_lines')
	product_brand_id = fields.Many2one('fischerbell.product.brand', 'Brand')
	use_customer_sku = fields.Boolean('Use Customer SKU', default=True)
	use_bp_code = fields.Boolean('Use BP code', default=True)
	use_product_batch_number = fields.Boolean('Use Product Batch Number', default=True)
	use_training = fields.Boolean('Use For Training')
	bp_code = fields.Char('BP Code')
	batch_number = fields.Char('Batch Number')
	customer_sku_ids = fields.One2many('customer.sku', 'product_tmpl_id', string="Customers")
	qr_code_image = fields.Binary(string='QR Code', attachment=True, readonly=True)
	tracking = fields.Selection([
		('serial', 'By Unique Serial Number'),
		('lot', 'By Batch'),
		('none', 'No Tracking')],
		string="Tracking", required=True, default='none', # Not having a default value here causes issues when migrating.
		compute='_compute_tracking', store=True, readonly=False, precompute=True,
		help="Ensure the traceability of a storable product in your warehouse.", copy=True)
	model = fields.Char('Model')
	terms_and_condition_ids = fields.Many2many(
		comodel_name='fischerbell.product.terms.and.conditions', 
		string='Terms & Conditions'
		)
	manufacturing_date = fields.Date('manufacturing date')
	expiration_date = fields.Date('expiration date')
	serial_number = fields.Char('Serial Number')
	requires_traceability = fields.Boolean('Requires Traceability')



	@api.depends_context('company')
	@api.depends('product_variant_ids', 'product_variant_ids.standard_price', 'purchase_line_ids')
	def _compute_standard_price(self):
		self.standard_price = 0
		for product in self:
			if product.purchase_line_ids:
				len_purchase = len(self.purchase_line_ids)
				total_purchase_price = 0
				for po in product.purchase_line_ids:
					total_purchase_price += po.price_unit

				average_cost = total_purchase_price / len_purchase
				product.standard_price = average_cost
			else:
				# Depends on force_company context because standard_price is company_dependent
				# on the product_product
				unique_variants = self.filtered(lambda template: len(template.product_variant_ids) == 1)
				for template in unique_variants:
					template.standard_price = template.product_variant_ids.standard_price
				for template in (self - unique_variants):
					template.standard_price = 0.0
	
	@api.depends('purchase_line_ids','purchase_line_ids.state','sales_line_ids','sales_line_ids.state')
	def _compute_lines(self):
		for product in self:
			product.purchase_lines_ids = [(6,0,product.purchase_line_ids.filtered(lambda x:x.state == 'purchase').ids)]
			product.sale_lines_ids = [(6,0,product.sales_line_ids.filtered(lambda x:x.state == 'sale').ids)]


	def generate_qr_code(self, data):
		# Assuming you have the URL as a string
		url = "http://13.214.221.125/web#cids=1&menu_id=312&action=519&model=product.template&view_type=form&id=124"

		# Parse the URL
		parsed_url = url_parse(url)

		# Get the parameters from the fragment (the part after '#')
		fragment_params = parsed_url.fragment.split('&')

		# Create a dictionary to store the parameters
		parameters = {}
		for param in fragment_params:
			key, value = param.split('=')
			parameters[key] = value

		# Retrieve the values of cids, menu_id, and action
		cids = parameters.get('cids')
		menu_id = parameters.get('menu_id')
		action = parameters.get('action')

		base_url = 'http://13.214.221.125'  # Replace with your Odoo website URL
		product_url = f'{base_url}/web#id={self.id}&menu_id={menu_id}&cids={cids}&action={action}&model=product.template&view_type=form'
		
		qr = qrcode.QRCode(
			version=1,
			error_correction=qrcode.constants.ERROR_CORRECT_L,
			box_size=5,
			border=4,
		)
		qr.add_data(product_url)
		qr.make(fit=True)
		img = qr.make_image(fill_color="black", back_color="white")

		# Save the QR code image to a BytesIO object
		img_buffer = io.BytesIO()
		img.save(img_buffer, format='PNG')
		img_data = base64.b64encode(img_buffer.getvalue())

		return img_data

	def write(self, vals):
		for product in self:
			if vals.get('barcode'):
				vals['qr_code_image'] = self.generate_qr_code(vals['barcode'])
			else:
				vals['qr_code_image'] = False

		res = super().write(vals)

		for product in self:
			if vals.get('list_price'):
				if vals['list_price'] > product.max_price:
					raise ValidationError("Sales price is greater than maximal price")
				if vals['list_price'] < product.min_price:
					raise ValidationError("Sales price is less than minimal price")

			if vals.get('max_price') and product.list_price > vals['max_price']:
				raise ValidationError("Sales price is greater than maximal price")

			if vals.get('min_price') and product.list_price < vals['min_price']:
				raise ValidationError("Sales price is less than minimal price")


		return res

	@api.model
	def create(self, vals):
		if vals.get('list_price') and vals.get('max_price') and vals.get('min_price'):
			if vals['list_price'] > vals['max_price']:
				raise ValidationError("Sales price is greater than maximal price")
			if vals['list_price'] < vals['min_price']:
				raise ValidationError("Sales price is less than minimal price")

		if vals.get('barcode'):
			vals['qr_code_image'] = self.generate_qr_code(vals['barcode'])
		else:
			vals['qr_code_image'] = False
		rec = super().create(vals)
		rec.requires_traceability = True
		return rec


class CustomerSku(models.Model):
	_name = 'customer.sku'
	_description = "Customer SKU"

	name = fields.Char('Name')
	customer_id = fields.Many2one('res.partner', 'Customer Name')
	product_tmpl_id = fields.Many2one('product.template', 'Product Template')
	customer_sku = fields.Char('Customer SKU')


class ProductCategory(models.Model):
	_inherit = 'product.category'

	is_training = fields.Boolean('Is Training')
	active = fields.Boolean('Active', default=True)


class ProductProduct(models.Model):
	_inherit = 'product.product'

	qr_code_image = fields.Binary(string='QR Code', attachment=True, readonly=True)
	product_detail_sheet = fields.Many2one('ir.attachment')
	product_detail_sheet_url = fields.Char('Sheet Url',compute="_compute_sheet_url")
	# requires_traceability = fields.Boolean('Requires Traceability')




	def _compute_sheet_url(self):
		base_url = self.env.company.get_base_url()
		for rec in self:
			if rec.product_detail_sheet:
				access_token = rec.product_detail_sheet.generate_access_token()
				url = f"{base_url}/web/content/?model=ir.attachment&id={rec.product_detail_sheet.id}&filename_field=name&access_token={access_token[0]}&field=datas&download=true"
				rec.product_detail_sheet_url = url
			else:
				rec.product_detail_sheet_url = ''



	def get_product_multiline_description_sale(self):
		""" Compute a multiline description of this product, in the context of sales
				(do not use for purchases or other display reasons that don't intend to use "description_sale").
			It will often be used as the default description of a sale order line referencing this product.
		"""
		name = self.name
		if self.description_sale:
			name += '\n' + self.description_sale

		return name


	def generate_qr_code(self, data):
		# Assuming you have the URL as a string
		url = "http://13.214.221.125/web#cids=1&menu_id=312&action=520&model=product.product&view_type=form&id=124"

		# Parse the URL
		parsed_url = url_parse(url)

		# Get the parameters from the fragment (the part after '#')
		fragment_params = parsed_url.fragment.split('&')

		# Create a dictionary to store the parameters
		parameters = {}
		for param in fragment_params:
			key, value = param.split('=')
			parameters[key] = value

		# Retrieve the values of cids, menu_id, and action
		cids = parameters.get('cids')
		menu_id = parameters.get('menu_id')
		action = parameters.get('action')

		base_url = 'http://13.214.221.125'  # Replace with your Odoo website URL
		product_url = f'{base_url}/web#id={self.id}&menu_id={menu_id}&cids={cids}&action={action}&model=product.product&view_type=form'
		
		qr = qrcode.QRCode(
			version=1,
			error_correction=qrcode.constants.ERROR_CORRECT_L,
			box_size=5,
			border=4,
		)
		qr.add_data(product_url)
		qr.make(fit=True)
		img = qr.make_image(fill_color="black", back_color="white")

		# Save the QR code image to a BytesIO object
		img_buffer = io.BytesIO()
		img.save(img_buffer, format='PNG')
		img_data = base64.b64encode(img_buffer.getvalue())

		return img_data

	def write(self, vals):
		for product in self:
			if vals.get('barcode'):
				vals['qr_code_image'] = self.generate_qr_code(vals['barcode'])
			else:
				vals['qr_code_image'] = False
		res = super().write(vals)
		return res

	@api.model
	def create(self, vals):
		if vals.get('barcode'):
			vals['qr_code_image'] = self.generate_qr_code(vals['barcode'])
		else:
			vals['qr_code_image'] = False
		rec =  super().create(vals)
		rec.requires_traceability = True
		return rec

