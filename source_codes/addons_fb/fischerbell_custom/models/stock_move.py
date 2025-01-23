# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api,fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta, date
import base64
from openpyxl import Workbook
from openpyxl.styles import Border, Side, Alignment, Font
from io import BytesIO
import xlrd
import xlsxwriter

class StockMove(models.Model):
	_inherit = "stock.move"

	customer_id = fields.Many2one('res.partner', 'Customer Name')
	phone = fields.Char('Contact', related="customer_id.phone")
	batch_number = fields.Char('Batch Number', related="customer_id.batch_number")
	lot_id = fields.Many2one('stock.lot', 'Serial Number')
	mrp_line_id = fields.Many2one('stock.move', compute="_compute_mrp_line_id", store=True)
	mrp_customer_id = fields.Many2one('res.partner', compute="_compute_mrp_line_id", store=True, string='Customer')
	mrp_phone = fields.Char('Phone Number', compute="_compute_mrp_line_id", store=True)
	manufacturing_date = fields.Date('manufacturing date')
	expiration_date = fields.Date('expiration date')
	serial_number = fields.Char('Serial Number')
	inventory_id = fields.Many2one('stock.inventory')
	upload_file = fields.Binary(string="Upload File")
	filename = fields.Char('Filename')
	
	def action_download_sample_file(self):
		wb = Workbook()
		ws = wb.active
		ws.title = "Sample"
		if self.product_id.use_expiration_date:
			headers = ['Lot/Serial No', 'Manufacturing Date', 'Expiry Date']
		else:
			headers = ['Lot/Serial No', 'Manufacturing Date']

		for col, header in enumerate(headers, start=1):
			ws.cell(row=1, column=col, value=header)
		
		fp = BytesIO()
		wb.save(fp)
		fp.seek(0)
		sample_data = fp.read()
		fp.close()
		
		wiz_id = self.env['download.report.wizard'].create({
			'file': base64.b64encode(sample_data)
		})
		return {
			'type': 'ir.actions.act_url',
			'url': 'web/content/?model=download.report.wizard&download=true&field=file&id=%s&filename=Sample.xlsx' % wiz_id.id,
			'target': 'self',
		}

	def upload_excel_file(self):
		self.ensure_one()

		if not self.upload_file:
			raise ValidationError("Please upload a file.")

		file_content = base64.b64decode(self.upload_file)

		workbook = xlrd.open_workbook(file_contents=file_content)
		sheet = workbook.sheet_by_index(0)

		total_demand = self.product_uom_qty
		created_lines_count = 0

		for row_idx in range(1, sheet.nrows):
			if created_lines_count >= total_demand:
				raise UserError(
				"The file has extra lots. Only %d are needed. Please adjust it."% total_demand
			)

			lot_name = sheet.cell(row_idx, 0).value
			manufacturing_date = sheet.cell(row_idx, 1).value
			expired_date = False
			if self.product_id.use_expiration_date:
				expired_date = sheet.cell(row_idx, 2).value



			if isinstance(manufacturing_date, (float, int)):
				manufacturing_date = datetime(1899, 12, 30) + timedelta(days=manufacturing_date)
				manufacturing_date = manufacturing_date.date()
			else:
				manufacturing_date = datetime.strptime(manufacturing_date, '%Y-%m-%d').date()

			if expired_date and isinstance(expired_date, (float, int)):
				expired_date = datetime(1899, 12, 30) + timedelta(days=expired_date)
				expired_date = expired_date.date()
			else:
				if expired_date:
					expired_date = datetime.strptime(expired_date, '%Y-%m-%d').date()


			company_id = self.env.user.company_id.id
			print("Company id = ",company_id)

			product_id = self.product_id.id
			print("Product id",product_id)


			lot = self.env['stock.lot'].search([('name', '=', lot_name)])
			if not lot:
				print("lot not found", lot)
				lot = self.env['stock.lot'].create({
				'name': lot_name,
				'product_id': product_id,
				'company_id': company_id,
				'expiration_date':expired_date,
				})

			else:
				raise UserError("A lot with the name '%s' for product '%s' has already been created." % (lot_name, self.product_id.name))


			self.env['stock.move.line'].create({
				'move_id': self.id,
				'product_id': product_id,
				'lot_id': lot.id,
				'qty_done': 1,
				'manufacturing_date': manufacturing_date,
				'expiration_date':expired_date,
				'picking_id':self.picking_id.id,
			})
			print("line create")
			created_lines_count += 1

		if self.picking_type_id.show_reserved:
			view = self.env.ref('stock.view_stock_move_operations')
			
		else:
			view = self.env.ref('stock.view_stock_move_nosuggest_operations')

		return {
			'name': _('Detailed Operations'),
			'type': 'ir.actions.act_window',
			'view_mode': 'form',
			'res_model': 'stock.move',
			'views': [(view.id, 'form')],
			'view_id': view.id,
			'target': 'new',
			'res_id': self.id,
		}



	@api.model
	def create(self, vals):
		# assigning the sequence for the record
		if self._context.get('inventory_id'):
			vals['inventory_id'] = self._context.get('inventory_id')
		res = super(StockMove, self).create(vals)
		return res

	def _get_new_picking_values(self):
		"""Inherit method for pass value from sale order to delivery order."""
		res = super(StockMove, self)._get_new_picking_values()
		res["delivery_instruction"] = self.group_id.sale_id.delivery_instruction
		res["artwork_attachment_ids"] = [(6, 0, self.group_id.sale_id.artwork_attachment_ids.ids)]
		return res

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

	def action_assign_serial_show_details(self):
		res = super(StockMove, self).action_assign_serial_show_details()
		for line in self.move_line_ids:
			line.update({'expiration_date':False})
		return res


class StockMoveLine(models.Model):
	_inherit = "stock.move.line"

	manufacturing_date = fields.Date('Manufacturing Date')
	expiration_date = fields.Date('Expiration Date')
	serial_number = fields.Char('Serial Number')
	batch_number = fields.Char('Batch Number')

	@api.onchange('expiration_date')
	def onchange_expiration_date(self):
		if self.expiration_date and self.expiration_date < date.today():
			raise ValidationError("Sorry, you cannot input the date which are previous date from the date of today ")
		if not self.lot_name:
			self.expiration_date = False

class StockWarehouseOrderpoint(models.Model):
	_inherit = "stock.warehouse.orderpoint"

	qty_on_hand = fields.Float('On Hand', readonly=True, compute='_compute_qty', digits='Product Unit of Measure',store=False)
	send_email_reorder = fields.Boolean('Send Email To Reorder', default=False)

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


