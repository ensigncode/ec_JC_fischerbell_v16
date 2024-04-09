from datetime import datetime
from odoo import models, tools

import io
import base64
import xlsxwriter
import mimetypes
import json

from odoo.tools.mimetypes import guess_mimetype

class FischerbellInventoryReport(models.AbstractModel):
	_name = 'report.fischerbell_custom.inventory_report'
	_inherit = 'report.report_xlsx.abstract'


	def generate_xlsx_report(self, workbook, data, product_template):
		sheet = workbook.add_worksheet('Inventory_Report')
		sheet.set_landscape()

		sheet.set_default_row(60)  # Default row height for all rows

		# Set column width
		sheet.set_column('A:A', 10)
		sheet.set_column('B:B', 12)
		sheet.set_column('C:C', 12)
		sheet.set_column('D:D', 60)
		sheet.set_column('E:E', 30)
		sheet.set_column('F:F', 20)
		sheet.set_column('G:G', 20)
		sheet.set_column('H:H', 20)
		sheet.set_column('I:I', 20)
		sheet.set_column('J:J', 12)
		sheet.set_column('K:K', 18)
		sheet.set_column('L:L', 12)
		sheet.set_column('M:M', 20)
		sheet.set_column('N:N', 30)
		sheet.set_column('O:O', 30)

		title1 = workbook.add_format()
		title1.set_bold()
		title1.set_align('center')
		title1.set_font_color('#FF0000')
		title1.set_underline()
		title2 = workbook.add_format()
		title2.set_bold()
		title2.set_border(1)
		title2.set_align('center')
		title2.set_align('vcenter')
		title2.set_text_wrap()
		title2.set_font_size(10)
		title2.set_bottom(5)
		content1 = workbook.add_format()
		content1.set_font_size(10)
		content1.set_border(1)
		content1.set_align('center')
		content1.set_align('vcenter')
		content1.set_text_wrap()
		content1.set_align('Arial')
		content2 = workbook.add_format()
		content2.set_border(1)
		content3 = workbook.add_format()
		content3.set_font_size(10)
		content3.set_align('left')
		content3.set_align('vcenter')
		content3.set_align('Arial')
		content4 = workbook.add_format()
		content4.set_bold()
		content4.set_italic(2)
		content4.set_font_size(10)
		content4.set_align('left')
		content4.set_align('vcenter')
		content4.set_align('Arial')
		content4.set_underline()
		content5 = workbook.add_format()
		content5.set_bold()
		content5.set_align('left')
		content5.set_align('Arial')
		content5.set_font_size(10)
		content5.set_font_color('#FF0000')
		content5.set_underline()

		# Define formats
		title_format = workbook.add_format({
			'bold': True,
			'align': 'center'})
		content_format = workbook.add_format({'font_size': 10, 'align': 'center', 'valign': 'vcenter', 'border': 1})

		# Write column headers
		headers = [
			'Item No', 'Brand', 'Item Group', 'Model# / Description', 'Stock on Hand Qty',
			'Reserved / Committed Qty', 'Unit of Measure', 'Purchase Price', 'Purchase Price Currency',
			'Inventory Price', 'Inventory Price Currency', 'Avg Price', 'Batch', 'Serial#', 'Expiry Date',
			'WH Location', 'Local / Overseas'
		]
		for col, header in enumerate(headers):
			sheet.write(0, col, header, title_format)

		# Initialize row and numbering variables
		row = 1
		numbering = 0

		# Iterate over product template
		for product in product_template:
			quant_id = self.env['stock.quant'].search(
				[('product_id', '=', product.product_variant_id.id)], order='id desc',limit=1)
			purchase_order_lines = self.env['purchase.order.line'].search(
				[('product_id', '=', product.product_variant_id.id)])
			stock_moves = self.env['stock.move'].search([('purchase_line_id', 'in', purchase_order_lines.ids)])

			if stock_moves:
				for move in stock_moves:
					stock_move_lines = move.move_line_ids.filtered(lambda ml: ml.product_id == product.product_variant_id)
					for stock_move_line in stock_move_lines:
						numbering += 1
						self.write_product_data(sheet, row, product, stock_move_line, content_format,quant_id)
						row += 1
			else:
				numbering += 1
				self.write_product_data(sheet, row, product, None, content_format,quant_id)
				row += 1

		for i in range(numbering):
			sheet.set_row(1 + i, 60)

	def write_product_data(self, sheet, row, product, stock_move_line, content_format,quant_id):
		if stock_move_line:

			if stock_move_line.move_id.purchase_line_id.order_id.currency_id.name != 'SGD':
				# Convert product price to SGD
				currency_rate = stock_move_line.move_id.purchase_line_id.order_id.currency_id._convert(1, self.env.ref(
					'base.SGD'), stock_move_line.move_id.purchase_line_id.order_id.company_id,
				                 stock_move_line.move_id.purchase_line_id.date_order)
				converted_price = product.list_price * currency_rate
			else:
				converted_price = product.list_price

			expiration_date = stock_move_line.expiration_date.strftime(
				'%Y-%m-%d') if stock_move_line.expiration_date else ''
			batch_number = stock_move_line.batch_number
			serial_number = stock_move_line.lot_name or ''  # Updated line

		else:
			expiration_date = ''
			batch_number = ''

			serial_number = ''
			converted_price = product.list_price


		data = [
			product.default_code or '', product.product_brand_id.name or '', product.categ_id.name or '',
			product.name or '', product.qty_available or '', product.virtual_available or '', product.uom_id.name or '',
			product.list_price or '',(stock_move_line.move_id.purchase_line_id.order_id.currency_id.name if stock_move_line else '')  or '', converted_price or '',   product.cost_currency_id.name or '', '',
			batch_number, serial_number, expiration_date, quant_id.location_id.location_id.name or ''
		]
		for col, value in enumerate(data):
			sheet.write(row, col, value, content_format)

		# Write "Local" or "Overseas" based on condition
		if stock_move_line and stock_move_line.move_id.picking_id.partner_id.l10n_in_gst_treatment == "overseas":
			sheet.write(row, col + 1, "Overseas", content_format)
		else:
			sheet.write(row, col + 1, "Local", content_format)


