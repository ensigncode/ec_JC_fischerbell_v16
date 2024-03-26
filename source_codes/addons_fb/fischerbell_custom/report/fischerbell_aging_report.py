from datetime import datetime, date
from odoo import models, tools
from dateutil.relativedelta import relativedelta
from bs4 import BeautifulSoup

import io
import base64
import xlsxwriter
import mimetypes
import json

from odoo.tools.mimetypes import guess_mimetype

class FischerbellAgingReport(models.AbstractModel):
	_name = 'report.fischerbell_custom.aging_report'
	_inherit = 'report.report_xlsx.abstract'



	def generate_xlsx_report(self, workbook, data, products):
		sheet = workbook.add_worksheet('Aging_Report')
		sheet.set_landscape()
		numbering = 0
		link = 0

		sheet.set_row(0, 20)
		sheet.set_column('A:A', 8)
		sheet.set_column('B:B', 12)
		sheet.set_column('C:C', 12)
		sheet.set_column('D:D', 12)
		sheet.set_column('E:E', 12)
		sheet.set_column('F:F', 13)
		sheet.set_column('G:G', 12)
		sheet.set_column('H:H', 12)
		sheet.set_column('I:I', 12)
		sheet.set_column('J:J', 12)
		sheet.set_column('K:K', 12)
		sheet.set_column('L:L', 12)
		sheet.set_column('M:M', 12)
		sheet.set_column('N:N', 12)
		sheet.set_column('O:O', 12)
		sheet.set_column('P:P', 12)
		sheet.set_column('Q:Q', 12)
		sheet.set_column('R:R', 12)
		sheet.set_column('S:S', 12)
		sheet.set_column('T:T', 12)
		sheet.set_column('U:U', 12)
		sheet.set_column('V:V', 12)
		sheet.set_column('W:W', 12)
		sheet.set_column('X:X', 12)
		sheet.set_column('Y:Y', 15)
		sheet.set_column('Z:Z', 15)
		sheet.set_column('AA:AA', 15)
		sheet.set_column('AB:AB', 15)
		sheet.set_column('AC:AC', 15)
		sheet.set_column('AD:AD', 15)
		sheet.set_column('AE:AE', 15)
		sheet.set_column('AF:AF', 15)
		sheet.set_column('AG:AG', 15)
		sheet.set_column('AH:AH', 15)
		sheet.set_column('AI:AI', 15)

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
		title2.set_bottom(1)
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



		x = 0
		y = 0
		sheet.write(y, x, '', title2)
		x += 1
		sheet.write(y, x, '', title2)
		x += 1
		sheet.write(y, x, '', title2)
		x += 1
		sheet.write(y, x, '', title2)
		x += 1
		sheet.write(y, x, '', title2)
		x += 1
		sheet.merge_range('F1:AI1', 'Aging Inventory', title2)
		# sheet.merge_range('F0:AI0', 'Aging Inventory', title2)

		# initial horizontal / vertical
		x = 0
		y = 1
	
		# write to cell
		sheet.write(y, x, 'Model', title2)
		x += 1
		sheet.write(y, x, 'Item Group', title2)
		x += 1
		sheet.write(y, x, 'Description', title2)
		x += 1
		sheet.write(y, x, 'Batch No', title2)
		x += 1
		sheet.write(y, x, 'Expiry Date', title2)
		x += 1
		sheet.write(y, x, 'Month 1_Qty', title2)
		x += 1
		sheet.write(y, x, 'Month 1_Value', title2)
		x += 1
		sheet.write(y, x, 'Month 2_Qty', title2)
		x += 1
		sheet.write(y, x, 'Month 2_Value', title2)
		x += 1
		sheet.write(y, x, 'Month 3_Qty', title2)
		x += 1
		sheet.write(y, x, 'Month 3_Value', title2)
		x += 1
		sheet.write(y, x, 'Month 4_Qty', title2)
		x += 1
		sheet.write(y, x, 'Month 4_Value', title2)
		x += 1
		sheet.write(y, x, 'Month 5_Qty', title2)
		x += 1
		sheet.write(y, x, 'Month 5_Value', title2)
		x += 1
		sheet.write(y, x, 'Month 6_Qty', title2)
		x += 1
		sheet.write(y, x, 'Month 6_Value', title2)
		x += 1
		sheet.write(y, x, 'Month 7_Qty', title2)
		x += 1
		sheet.write(y, x, 'Month 7_Value', title2)
		x += 1
		sheet.write(y, x, 'Month 8_Qty', title2)
		x += 1
		sheet.write(y, x, 'Month 8_Value', title2)
		x += 1
		sheet.write(y, x, 'Month 9_Qty', title2)
		x += 1
		sheet.write(y, x, 'Month 9_Value', title2)
		x += 1
		sheet.write(y, x, 'Month 10_Qty', title2)
		x += 1
		sheet.write(y, x, 'Month 10_Value', title2)
		x += 1
		sheet.write(y, x, 'Month 11_Qty', title2)
		x += 1
		sheet.write(y, x, 'Month 11_Value', title2)
		x += 1
		sheet.write(y, x, 'Month 12_Qty', title2)
		x += 1
		sheet.write(y, x, 'Month 12_Value', title2)
		x += 1
		sheet.write(y, x, '>1yr_Qty', title2)
		x += 1
		sheet.write(y, x, '>1yr_Value', title2)
		x += 1
		sheet.write(y, x, 'UOM', title2)
		x += 1
		sheet.write(y, x, 'Total Qty', title2)
		x += 1
		sheet.write(y, x, 'PO Currency', title2)
		x += 1
		sheet.write(y, x, 'Total Price', title2)
		x += 1

		lot_serial_numbers = False
		purchase_orders = self.env['purchase.order'].search([])
		# for product in products:
		# 	lot_serial_numbers = self.env['stock.lot'].search([('product_id','=',product.id)])

		x = 0
		y += 1
		if purchase_orders:
			for order in purchase_orders:
				total_qty = 0
				total_price = 0
				numbering += 1
				sheet.write(y, x, order.product_id.model or '', content1) #Model
				x += 1
				sheet.write(y, x, order.product_id.default_code or '', content1) #Item Group
				x += 1
				description = order.product_id.description
				soup = BeautifulSoup(description, 'html.parser')
				DescriptionText = soup.get_text()
				sheet.write(y, x, DescriptionText or '', content1) #description
				x += 1
				sheet.write(y, x, order.name or '', content1) #Batch No
				x += 1
				if order.expiration_date:
					sheet.write(y, x, order.expiration_date.strftime('%d %b %Y') or '', content1) #Expiration Date
					x += 1
				else:
					sheet.write(y, x, '', content1)
					x += 1
				today = datetime.now()
				expiry_1_month = today + relativedelta(months=1)
				expiry_2_month = today + relativedelta(months=2)
				expiry_3_month = today + relativedelta(months=3)
				expiry_4_month = today + relativedelta(months=4)
				expiry_5_month = today + relativedelta(months=5)
				expiry_6_month = today + relativedelta(months=6)
				expiry_7_month = today + relativedelta(months=7)
				expiry_8_month = today + relativedelta(months=8)
				expiry_9_month = today + relativedelta(months=9)
				expiry_10_month = today + relativedelta(months=10)
				expiry_11_month = today + relativedelta(months=11)
				expiry_12_month = today + relativedelta(months=12)
				expiry_1_year = today + relativedelta(years=1)

				#1 month qty
				if order.expiration_date <= expiry_1_month:
					total_qty += 1
					sheet.write(y, x, order.product_qty or '', content1)
					x += 1
				else:
					sheet.write(y, x, '', content1)
					x += 1
				#1 month value
				if order.expiration_date <= expiry_1_month:
					total_price += 1
					sheet.write(y, x, order.product_id.list_price or '', content1)
					x += 1
				else:
					sheet.write(y, x, '', content1)
					x += 1

				###############################################################

				#2 month qty
				if order.expiration_date <= expiry_2_month and order.expiration_date > expiry_1_month:
					total_qty += 1
					sheet.write(y, x, order.product_qty or '', content1)
					x += 1
				else:
					sheet.write(y, x, '', content1)
					x += 1
				#2 month value
				if order.expiration_date <= expiry_2_month and order.expiration_date >= expiry_1_month:
					total_price += 1
					sheet.write(y, x, order.product_id.list_price or '', content1)
					x += 1
				else:
					sheet.write(y, x, '', content1)
					x += 1

				###############################################################

				#3 month qty
				if order.expiration_date <= expiry_3_month and order.expiration_date > expiry_2_month:
					total_qty += 1
					sheet.write(y, x, order.product_qty or '', content1)
					x += 1
				else:
					sheet.write(y, x, '', content1)
					x += 1
				#3 month value
				if order.expiration_date <= expiry_3_month and order.expiration_date > expiry_2_month:
					total_price += 1
					sheet.write(y, x, order.product_id.list_price or '', content1)
					x += 1
				else:
					sheet.write(y, x, '', content1)
					x += 1

				###############################################################

				#4 month qty
				if order.expiration_date <= expiry_4_month and order.expiration_date > expiry_3_month:
					total_qty += 1
					sheet.write(y, x, order.product_qty or '', content1)
					x += 1
				else:
					sheet.write(y, x, '', content1)
					x += 1
				#4 month value
				if order.expiration_date <= expiry_4_month and order.expiration_date > expiry_3_month:
					total_price += 1
					sheet.write(y, x, order.product_id.list_price or '', content1)
					x += 1
				else:
					sheet.write(y, x, '', content1)
					x += 1

				###############################################################

				#5 month qty
				if order.expiration_date <= expiry_5_month and order.expiration_date > expiry_4_month:
					total_qty += 1
					sheet.write(y, x, order.product_qty or '', content1)
					x += 1
				else:
					sheet.write(y, x, '', content1)
					x += 1
				#5 month value
				if order.expiration_date <= expiry_5_month and order.expiration_date > expiry_4_month:
					total_price += 1
					sheet.write(y, x, order.product_id.list_price or '', content1)
					x += 1
				else:
					sheet.write(y, x, '', content1)
					x += 1

				###############################################################

				#6 month qty
				if order.expiration_date <= expiry_6_month and order.expiration_date > expiry_5_month:
					total_qty += 1
					sheet.write(y, x, order.product_qty or '', content1)
					x += 1
				else:
					sheet.write(y, x, '', content1)
					x += 1
				#6 month value
				if order.expiration_date <= expiry_6_month and order.expiration_date > expiry_5_month:
					total_price += 1
					sheet.write(y, x, order.product_id.list_price or '', content1)
					x += 1
				else:
					sheet.write(y, x, '', content1)
					x += 1

				###############################################################

				#7 month qty
				if order.expiration_date <= expiry_7_month and order.expiration_date > expiry_6_month:
					total_qty += 1
					sheet.write(y, x, order.product_qty or '', content1)
					x += 1
				else:
					sheet.write(y, x, '', content1)
					x += 1
				#7 month value
				if order.expiration_date <= expiry_7_month and order.expiration_date > expiry_6_month:
					total_price += 1
					sheet.write(y, x, order.product_id.list_price or '', content1)
					x += 1
				else:
					sheet.write(y, x, '', content1)
					x += 1

				###############################################################

				#8 month qty
				if order.expiration_date <= expiry_8_month and order.expiration_date > expiry_7_month:
					total_qty += 1
					sheet.write(y, x, order.product_qty or '', content1)
					x += 1
				else:
					sheet.write(y, x, '', content1)
					x += 1
				#8 month value
				if order.expiration_date <= expiry_8_month and order.expiration_date > expiry_7_month:
					total_price += 1
					sheet.write(y, x, order.product_id.list_price or '', content1)
					x += 1
				else:
					sheet.write(y, x, '', content1)
					x += 1

				###############################################################

				#9 month qty
				if order.expiration_date <= expiry_9_month and order.expiration_date > expiry_8_month:
					total_qty += 1
					sheet.write(y, x, order.product_qty or '', content1)
					x += 1
				else:
					sheet.write(y, x, '', content1)
					x += 1
				#9 month value
				if order.expiration_date <= expiry_9_month and order.expiration_date > expiry_8_month:
					total_price += 1
					sheet.write(y, x, order.product_id.list_price or '', content1)
					x += 1
				else:
					sheet.write(y, x, '', content1)
					x += 1

				###############################################################

				#110month qty
				if order.expiration_date <= expiry_10_month and order.expiration_date > expiry_9_month:
					total_qty += 1
					sheet.write(y, x, order.product_qty or '', content1)
					x += 1
				else:
					sheet.write(y, x, '', content1)
					x += 1
				#10 month value
				if order.expiration_date <= expiry_10_month and order.expiration_date > expiry_9_month:
					total_price += 1
					sheet.write(y, x, order.product_id.list_price or '', content1)
					x += 1
				else:
					sheet.write(y, x, '', content1)
					x += 1

				###############################################################

				#11 month qty
				if order.expiration_date <= expiry_11_month and order.expiration_date > expiry_10_month:
					total_qty += 1
					sheet.write(y, x, order.product_qty or '', content1)
					x += 1
				else:
					sheet.write(y, x, '', content1)
					x += 1
				#11 month value
				if order.expiration_date <= expiry_11_month and order.expiration_date > expiry_10_month:
					total_price += 1
					sheet.write(y, x, order.product_id.list_price or '', content1)
					x += 1
				else:
					sheet.write(y, x, '', content1)
					x += 1

				###############################################################

				#12 month qty
				if order.expiration_date <= expiry_12_month and order.expiration_date > expiry_11_month:
					total_qty += 1
					sheet.write(y, x, order.product_qty or '', content1)
					x += 1
				else:
					sheet.write(y, x, '', content1)
					x += 1
				#12 month value
				if order.expiration_date <= expiry_12_month and order.expiration_date > expiry_11_month:
					total_price += 1
					sheet.write(y, x, order.product_id.list_price or '', content1)
					x += 1
				else:
					sheet.write(y, x, '', content1)
					x += 1

				###############################################################

				#1 year qty
				if order.expiration_date <= expiry_1_year and order.expiration_date > expiry_12_month:
					total_qty += 1
					sheet.write(y, x, order.product_qty or '', content1)
					x += 1
				else:
					sheet.write(y, x, '', content1)
					x += 1
				#1 year value
				if order.expiration_date <= expiry_1_year and order.expiration_date > expiry_12_month:
					total_price += 1
					sheet.write(y, x, order.product_id.list_price or '', content1)
					x += 1
				else:
					sheet.write(y, x, '', content1)
					x += 1

				sheet.write(y, x, order.product_uom_id.name or '', content1) #UoM
				x += 1
				sheet.write(y, x, total_qty or '', content1) #Total Qty
				x += 1
				sheet.write(y, x, '', content1) #PO Currency
				x += 1
				sheet.write(y, x, '', content1) #Total Price
				x += 1

				print(total_qty, 'total_qty=============')
				print(total_price, 'total_qty=============')

				x = 0
				y += 1
			total_qty = 0
			total_price = 0
			for i in range(numbering):
				sheet.set_row(2+i, 50)
