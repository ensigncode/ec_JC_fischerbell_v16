from datetime import datetime
from odoo import models, tools

import io
import base64
import xlsxwriter
import mimetypes
import json

from odoo.tools.mimetypes import guess_mimetype

class FischerbellInstrumentRentalTc(models.AbstractModel):
	_name = 'report.fischerbell_custom.instrument_rental_tc'
	_inherit = 'report.report_xlsx.abstract'


	def generate_xlsx_report(self, workbook, data, sale_order):
		sheet = workbook.add_worksheet('Instrument_Rental_TC')
		sheet.set_landscape()

		sheet.set_default_row(60)  # Default row height for all rows

		# Set column width
		sheet.set_column('A:A', 60)
		sheet.set_column('B:B', 12)

		title1 = workbook.add_format()
		title1.set_bold()
		title1.set_align('center')
		title1.set_font_color('#FF0000')
		title1.set_underline()

		# Define formats
		title_format = workbook.add_format({
			'bold': True,
			'align': 'center'})
		content_format = workbook.add_format({'font_size': 10, 'align': 'center', 'valign': 'vcenter', 'border': 1})

		# Write column headers
		headers = [
			'Terms and Conditions of Rental of Equipment and Instrument '
		]
		for col, header in enumerate(headers):
			sheet.write(0, col, header, title_format)

		# Initialize row and numbering variables
		row = 1
		numbering = 0

		# Iterate over product template
		for product in sale_order:
			pass
		# 	purchase_order_lines = self.env['purchase.order.line'].search(
		# 		[('product_id', '=', product.product_variant_id.id)])
		# 	stock_moves = self.env['stock.move'].search([('purchase_line_id', 'in', purchase_order_lines.ids)])
		#
		# 	if stock_moves:
		# 		for move in stock_moves:
		# 			stock_move_lines = move.move_line_ids.filtered(lambda ml: ml.product_id == product.product_variant_id)
		# 			for stock_move_line in stock_move_lines:
		# 				numbering += 1
		# 				self.write_product_data(sheet, row, product, stock_move_line, content_format)
		# 				row += 1
		# 	else:
		# 		numbering += 1
		# 		self.write_product_data(sheet, row, product, None, content_format)
		# 		row += 1
		#
		# for i in range(numbering):
		# 	sheet.set_row(1 + i, 60)
