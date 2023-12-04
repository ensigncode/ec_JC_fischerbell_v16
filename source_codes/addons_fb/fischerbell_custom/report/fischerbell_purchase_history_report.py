from datetime import datetime
from odoo import models, tools

import io
import base64
import xlsxwriter
import mimetypes
import json

from odoo.tools.mimetypes import guess_mimetype

class FischerbellPurchaseHistoryReport(models.AbstractModel):
	_name = 'report.fischerbell_custom.purchase_history_report'
	_inherit = 'report.report_xlsx.abstract'



	def generate_xlsx_report(self, workbook, data, product_template):
		sheet = workbook.add_worksheet('Purchase_History_Report')
		sheet.set_landscape()
		numbering = 0
		link = 0


		sheet.set_row(0, 60)
		sheet.set_column('A:A', 4)
		sheet.set_column('B:B', 12)
		sheet.set_column('C:C', 12)
		sheet.set_column('D:D', 20)
		sheet.set_column('E:E', 10)
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
		sheet.write(y, x, 'Supplier', title2)
		x += 1
		sheet.write(y, x, 'PO No', title2)
		x += 1
		sheet.write(y, x, 'Model No', title2)
		x += 1
		sheet.write(y, x, 'Description', title2)
		x += 1
		sheet.write(y, x, 'Qty', title2)
		x += 1
		sheet.write(y, x, 'UOM', title2)
		x += 1
		sheet.write(y, x, 'Purchase Price', title2)
		x += 1
		sheet.write(y, x, 'Currency', title2)
		x += 1
		sheet.write(y, x, 'Total Price', title2)
		x += 1
		sheet.write(y, x, 'Total Price (SGD)', title2)
		x += 1
		sheet.write(y, x, 'Last Purchase Date', title2)
		x += 1
		sheet.write(y, x, 'Last Receipt Date', title2)
		x += 1
		sheet.write(y, x, 'TEXT/REMARKS', title2)
		x += 1
		sheet.write(y, x, 'Oversea / Local Supplier', title2)
		x += 1

		x = 0
		y += 1
		numbering = 0
		for product in product_template:
			for line in product.purchase_line_ids:
				numbering += 1
				sheet.write(y, x, line.partner_id.name or '', content1) #Supplier
				x += 1
				sheet.write(y, x, line.order_id.name or '', content1) #PO Number
				x += 1
				sheet.write(y, x, line.product_template_id.model or '', content1) #Product / Model No
				x += 1
				sheet.write(y, x, line.name or '', content1) #Description
				x += 1
				sheet.write(y, x, line.product_uom_qty or '', content1) #Qty
				x += 1
				sheet.write(y, x, line.product_uom.name or '', content1) #UOM
				x += 1
				sheet.write(y, x, line.price_unit or '', content1) #Purchase Price
				x += 1
				sheet.write(y, x, line.currency_id.name or '', content1) #Currency
				x += 1
				sheet.write(y, x, line.price_total or '', content1) #Total Price
				x += 1

				total_price = []
				total_price_sgd = ''
				productprice = line.currency_id._convert(line.price_total,line.company_id.currency_id,line.company_id,datetime.utcnow()) 
				total_price.append({'price':line.price_total})
				for data in total_price:
					total_price_sgd = '{:.2f}'.format(data['price'])
				sheet.write(y, x, str(total_price_sgd), content1) #Total Price in SGD
				x += 1

				sheet.write(y, x, line.date_order.strftime('%d %b %Y') or '', content1) #Last Purchase Date
				x += 1

				date = ''
				for move in line.move_ids:
					if move.picking_id.date_done:
						date = move.picking_id.date_done.strftime('%d %b %Y')
					else:
						date = ''
				sheet.write(y, x, date or '', content1) #Last Receipt Date
				x += 1				

				sheet.write(y, x, line.order_id.internal_note or '', content1) #TEXT / REMARKS
				x += 1
				if line.order_id.partner_id.currency_type:
					sheet.write(y, x, line.order_id.partner_id.currency_type, content1) #Oversea / Local Supplier
				else:
					sheet.write(y, x, '', content1) #Oversea / Local Supplier
				x += 1

				x = 0	
				y += 1
		for i in range(numbering):
			sheet.set_row(1+i, 60)