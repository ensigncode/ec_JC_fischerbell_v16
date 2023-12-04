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
			all_purchase_line = 0
			avg_price = 0
			len_purchase = []

			for purchase_line in product.purchase_line_ids:
				len_purchase.append(purchase_line.id)
				all_purchase_line += purchase_line.price_unit

			if all_purchase_line and len_purchase:
				avg_price = all_purchase_line / len(len_purchase)

			for line in product.purchase_line_ids:
				numbering += 1
				sheet.write(y, x, line.product_template_id.default_code or '', content1) #Supplier
				x += 1
				sheet.write(y, x, line.product_template_id.product_brand_id.name or '', content1) #PO Number
				x += 1
				sheet.write(y, x, line.product_template_id.categ_id.name or '', content1) #Product / Model No
				x += 1
				sheet.write(y, x, line.product_template_id.model or '', content1) #Description
				x += 1
				sheet.write(y, x, line.product_uom_qty or '', content1) #Qty
				x += 1
				sheet.write(y, x, line.product_uom.name or '', content1) #UOM
				x += 1
				sheet.write(y, x, product.standard_price or '', content1) #Purchase Price / Cost Price
				x += 1
				sheet.write(y, x, product.cost_currency_id.name or '', content1) #Purchase Currency / Cost Currency
				x += 1
				sheet.write(y, x, product.list_price or '', content1) #Inventory Price / Sales Price
				x += 1
				sheet.write(y, x, product.currency_id.name or '', content1) #Inventory Currency / Sales Currency
				x += 1
				if avg_price:
					sheet.write(y, x, avg_price or '', content1) #Avg Price
					x += 1
				else:
					sheet.write(y, x, '', content1) #Avg Price
					x += 1

				if line.product_template_id.tracking == 'lot':
					sheet.write(y, x, line.lot_id.name or '', content1) #Batch Number
				else:
					sheet.write(y, x, '', content1) #Batch Number
				x += 1

				if line.product_template_id.tracking == 'serial':
					sheet.write(y, x, line.lot_id.name or '', content1) #Serial
				else:
					sheet.write(y, x, '', content1) #Serial
				x += 1

				expiry_date = ''
				wh_location = ''
				for receipt in line.order_id.picking_ids:
					if receipt.date_deadline:
						expiry_date = receipt.date_deadline.strftime('%d %b %Y')
					else:
						expiry_date = ''

					if receipt.location_dest_id:
						wh_location = receipt.location_dest_id.complete_name
					else:
						wh_location = ''
				sheet.write(y, x, expiry_date, content1) #Expiry Date
				x += 1
				sheet.write(y, x, wh_location, content1) #WH Location
				x += 1
				# freight_charge = 0
				for bill in line.order_id.invoice_ids:
					for charges in bill.move_ids:
						sheet.write(y, x, charges.name or '', content1) #Freight Charges
				x += 1
				if line.order_id.partner_id.currency_type:
					sheet.write(y, x, line.order_id.partner_id.currency_type, content1) #Local / Overseas
				else:
					sheet.write(y, x, '', content1) #Local / Overseas
				x += 1

				x = 0
				y += 1
		for i in range(numbering):
			sheet.set_row(1+i, 60)