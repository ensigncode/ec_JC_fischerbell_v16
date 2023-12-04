from datetime import datetime
from odoo import models, tools

import io
import base64
import xlsxwriter
import mimetypes
import json

from odoo.tools.mimetypes import guess_mimetype

class FischerbellDeliveryOrderReport(models.AbstractModel):
	_name = 'report.fischerbell_custom.delivery_order_report'
	_inherit = 'report.report_xlsx.abstract'



	def generate_xlsx_report(self, workbook, data, stock_picking):
		sheet = workbook.add_worksheet('Delivery_Order_Report')
		sheet.set_landscape()
		numbering = 0
		link = 0
	

		# sheet.set_row(0, 60)
		# sheet.set_column('A:A', 12)
		# sheet.set_column('B:B', 12)
		# sheet.set_column('C:C', 12)
		# sheet.set_column('D:D', 20)
		# sheet.set_column('E:E', 10)
		# sheet.set_column('F:F', 10)
		# sheet.set_column('G:G', 12)
		# sheet.set_column('H:H', 12)
		# sheet.set_column('I:I', 10)
		# sheet.set_column('J:J', 12)
		# sheet.set_column('K:K', 18)
		# sheet.set_column('L:L', 8)
		# sheet.set_column('M:M', 12)
		# sheet.set_column('N:N', 8)
		# sheet.set_column('O:O', 12)

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
		content4.set_font_size(8)
		content4.set_align('left')
		content4.set_align('vcenter')
		content4.set_align('Arial')
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
		image = io.BytesIO(base64.b64decode(stock_picking.company_id.logo))
		sheet.insert_image(y, x ,"image.png", {'image_data': image,  'x_scale': 0.2, 'y_scale': 0.2})


		x = 0
		y += 3
		sheet.write(y, x, 'Delivery Order', content4)
		x += 4
		sheet.write(y, x, 'DO No. : ', content4)
