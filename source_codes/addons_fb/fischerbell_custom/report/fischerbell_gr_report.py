from datetime import datetime
from odoo import models, tools

import io
import base64
import xlsxwriter
import mimetypes
import json

from odoo.tools.mimetypes import guess_mimetype

class FischerbellGrReport(models.AbstractModel):
	_name = 'report.fischerbell_custom.gr_report'
	_inherit = 'report.report_xlsx.abstract'



	def generate_xlsx_report(self, workbook, data, picking):
		sheet = workbook.add_worksheet('GR_Report')
		sheet.set_landscape()
		numbering = 0
		link = 0


		sheet.set_row(0, 60)
		sheet.set_column('A:A', 12)
		sheet.set_column('B:B', 12)
		sheet.set_column('C:C', 12)
		sheet.set_column('D:D', 20)
		sheet.set_column('E:E', 10)
		sheet.set_column('F:F', 10)
		sheet.set_column('G:G', 12)
		sheet.set_column('H:H', 12)
		sheet.set_column('I:I', 10)
		sheet.set_column('J:J', 12)

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
		sheet.write(y, x, 'GR Date', title2)
		x += 1
		sheet.write(y, x, 'Supplier Name', title2)
		x += 1
		sheet.write(y, x, 'PO No', title2)
		x += 1
		sheet.write(y, x, 'Model No', title2)
		x += 1
		sheet.write(y, x, 'Description', title2)
		x += 1
		sheet.write(y, x, 'Qty', title2)
		x += 1
		sheet.write(y, x, 'PO Price', title2)
		x += 1
		sheet.write(y, x, 'UOM', title2)
		x += 1
		sheet.write(y, x, 'Total Price', title2)
		x += 1
		sheet.write(y, x, 'Buyer Name', title2)
		x += 1

		x = 0
		y += 1
		numbering = 0
		for pick in picking:
			for move in pick.move_ids_without_package:
				numbering += 1

				date_done = ''
				if move.picking_id.date_done:
					date_done = move.picking_id.date_done.strftime('%d %b %Y')
				else:
					date_done = ''
				sheet.write(y, x, date_done or '', content1) #GR Date
				x += 1
				sheet.write(y, x, move.purchase_line_id.order_id.partner_id.name or '', content1) #Supplier Name
				x += 1
				sheet.write(y, x, move.purchase_line_id.order_id.name or '', content1) #PO No
				x += 1
				sheet.write(y, x, move.product_id.model or '', content1) #Model No
				x += 1
				sheet.write(y, x, move.description_picking or '', content1) #Description
				x += 1
				sheet.write(y, x, move.product_uom_qty or '', content1) #QTY
				x += 1
				sheet.write(y, x, move.purchase_line_id.price_unit or '', content1) #PO Price
				x += 1
				sheet.write(y, x, move.purchase_line_id.product_uom.name or '', content1) #UOM
				x += 1
				total_price = move.purchase_line_id.product_uom_qty * move.purchase_line_id.price_unit or ''
				sheet.write(y, x, total_price, content1) #Total Price
				x += 1
				sheet.write(y, x, move.purchase_line_id.order_id.user_id.name or '', content1) #Buyer Name
				x += 1

				x = 0
				y += 1
		for i in range(numbering):
			sheet.set_row(1+i, 60)