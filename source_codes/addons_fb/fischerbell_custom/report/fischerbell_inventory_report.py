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
		numbering = 0
		link = 0


		sheet.set_row(0, 60)
		sheet.set_column('A:A', 10)
		sheet.set_column('B:B', 12)
		sheet.set_column('C:C', 12)
		sheet.set_column('D:D', 20)
		sheet.set_column('E:E', 4)
		sheet.set_column('F:F', 10)
		sheet.set_column('G:G', 12)
		sheet.set_column('H:H', 12)
		sheet.set_column('I:I', 10)
		sheet.set_column('J:J', 12)
		sheet.set_column('K:K', 18)
		sheet.set_column('L:L', 8)
		sheet.set_column('M:M', 12)
		sheet.set_column('N:N', 8)
		sheet.set_column('O:O', 12)

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


		# initial horizontal / vertical
		x = 0
		y = 0

		# write to cell
		sheet.write(y, x, 'Item No', title2)
		x += 1
		sheet.write(y, x, 'Brand', title2)
		x += 1
		sheet.write(y, x, 'Item Group', title2)
		x += 1
		sheet.write(y, x, 'Model# / Description', title2)
		x += 1
		sheet.write(y, x, 'Qty', title2)
		x += 1
		sheet.write(y, x, 'Unit of Measure', title2)
		x += 1
		sheet.write(y, x, 'Purchase Price', title2)
		x += 1
		sheet.write(y, x, 'Purchase Price Currency', title2)
		x += 1
		sheet.write(y, x, 'Inventory Price', title2)
		x += 1
		sheet.write(y, x, 'Inventory Price Currency', title2)
		x += 1
		sheet.write(y, x, 'Avg Price', title2)
		x += 1
		sheet.write(y, x, 'Batch', title2)
		x += 1
		sheet.write(y, x, 'Serial#', title2)
		x += 1
		sheet.write(y, x, 'Expiry Date', title2)
		x += 1
		sheet.write(y, x, 'WH Location', title2)
		x += 1
		sheet.write(y, x, 'Freight Charges', title2)
		x += 1
		sheet.write(y, x, 'Local / Overseas', title2)
		x += 1

		x = 0
		y += 1
		numbering = 0

		for product in product_template:
			expiration_date = product.expiration_date.strftime('%Y-%m-%d') if product.expiration_date else ''
			numbering += 1
			sheet.write(y, x,  product.default_code or '', content1)
			x += 1
			sheet.write(y, x, product.product_brand_id.name or '', content1)
			x += 1
			sheet.write(y, x, product.categ_id.name or '', content1)
			x += 1
			sheet.write(y, x, product.name or '', content1)
			x += 1
			sheet.write(y, x, product.qty_available or '', content1)
			x += 1
			sheet.write(y, x, product.uom_id.name or '', content1)
			x += 1
			sheet.write(y, x, product.standard_price or '', content1)
			x += 1
			sheet.write(y, x, product.cost_currency_id.name or '', content1)
			x += 1
			sheet.write(y, x,  '', content1)
			x += 1
			sheet.write(y, x, product.currency_id.name or '', content1)
			x += 1
			sheet.write(y, x,  '', content1)
			x += 1
			sheet.write(y, x, product.batch_number or '', content1)
			x += 1
			sheet.write(y, x, product.serial_number or '', content1)
			x += 1
			sheet.write(y, x, expiration_date or '', content1)
			x += 1
			sheet.write(y, x, product.location_id.name or '', content1)
			x += 1
			sheet.write(y, x, '', content1)
			x += 1
			sheet.write(y, x, '', content1)
			x += 1

			x = 0
			y += 1
		for i in range(numbering):
			sheet.set_row(1+i, 60)