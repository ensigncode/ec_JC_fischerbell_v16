from datetime import datetime
from odoo import models, tools

import io
import base64
import xlsxwriter
import mimetypes
import json

from odoo.tools.mimetypes import guess_mimetype

class FischerbellLoanItemReport(models.AbstractModel):
	_name = 'report.fischerbell_custom.loan_item_report'
	_inherit = 'report.report_xlsx.abstract'



	def generate_xlsx_report(self, workbook, data, sale_order_line):
		sheet = workbook.add_worksheet('Loan_Items_Report')
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
		sheet.set_column('N:N', 10)
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
		sheet.write(y, x, 'S/N', title2)
		x += 1
		sheet.write(y, x, 'Customer Code', title2)
		x += 1
		sheet.write(y, x, 'Customer', title2)
		x += 1
		sheet.write(y, x, 'Contact Person', title2)
		x += 1
		sheet.write(y, x, 'Ship To', title2)
		x += 1
		sheet.write(y, x, 'T Loan Date', title2)
		x += 1
		sheet.write(y, x, 'SO Number', title2)
		x += 1
		sheet.write(y, x, 'SO Date', title2)
		x += 1
		sheet.write(y, x, 'T-Loan Number', title2)
		x += 1
		sheet.write(y, x, 'SKU', title2)
		x += 1
		sheet.write(y, x, 'Product Name', title2)
		x += 1
		sheet.write(y, x, 'Qty', title2)
		x += 1
		sheet.write(y, x, 'Location (Warehouse)', title2)
		x += 1
		sheet.write(y, x, 'Status', title2)
		x += 1
		sheet.write(y, x, 'Billing Status', title2)
		x += 1

		x = 0
		y += 1
		numbering = 0
		for line in sale_order_line:
			numbering += 1
			sheet.write(y, x, numbering, content1) #S/N 
			x += 1
			if line.order_id.partner_id.customer_code:
				sheet.write(y, x, line.order_id.partner_id.customer_code, content1) #Customer Code
				x += 1
			else:
				sheet.write(y, x, '', content1) #Customer Code
				x += 1
			sheet.write(y, x, line.order_id.partner_id.name , content1) #Customer 
			x += 1
			contact_person = ''
			if line.order_id.partner_id.child_ids:
				for child in line.order_id.partner_id.child_ids:
					if not child.name:
						contact_person = ''
					else:
						contact_person += child.name + ', '
			else:
				contact_person += line.order_id.partner_id.name
			if contact_person:
				sheet.write(y, x, contact_person , content1) #Contact Person
				x += 1
			else:
				sheet.write(y, x, '' , content1) #Contact Person
				x += 1
			sheet.write(y, x, line.order_id.partner_shipping_id.name , content1) #Ship To
			x += 1
			if line.order_id.date_order:
				sheet.write(y, x, line.order_id.date_order.strftime('%d %b %Y'), content1) #T Loan
				x += 1
			else:
				sheet.write(y, x, '', content1) #T Loan
				x += 1

			if line.order_id.sale_id.name:
				sheet.write(y, x, line.order_id.sale_id.name , content1) #Date SO Number
				x += 1
			else:
				sheet.write(y, x, '' , content1) #Date SO Number
				x += 1

			if line.order_id.sale_id.date_order:
				sheet.write(y, x, line.order_id.sale_id.date_order.strftime('%d %b %Y') , content1) #SO Date
				x += 1
			else:
				sheet.write(y, x, '' , content1) #SO Date
				x += 1
			if line.order_id.name:
				sheet.write(y, x, line.order_id.name , content1) #T-Loan Number
				x += 1
			else:
				sheet.write(y, x, '' , content1) #T-Loan Number
				x += 1
			if line.product_id.default_code:
				sheet.write(y, x, line.product_id.default_code , content1) #SKU
				x += 1
			else:
				sheet.write(y, x, '', content1) #SKU
				x += 1
			sheet.write(y, x, line.product_id.name , content1) #Product Name
			x += 1
			sheet.write(y, x, line.product_uom_qty , content1) #Qty
			x += 1
			sheet.write(y, x, line.order_id.warehouse_id.name , content1) #Location (Warehouse)
			x += 1

			if line.order_id.loan_date:
				loan_date = line.order_id.loan_date.strftime('%d %b %Y')
				loan_state = line.order_id.loan_state + '\n' + loan_date
				sheet.write(y, x, loan_state , content1) #Status
				x += 1
			else:
				sheet.write(y, x, line.order_id.loan_state , content1) #Status
				x += 1
			billing_status = ''
			if line.order_id.invoice_status == 'invoiced':
				list_invoices = ''
				list_date = ''
				for inv in line.order_id.invoice_ids:
					if inv.payment_state in ['in_payment','paid']:
						list_invoices += inv.name + ', '
						list_date += inv.invoice_date.strftime("%d-%m-%Y") + ', '
					else:
						pass
				billing_status = str(line.order_id.billing_state)+', ' +list_invoices +list_date
			else:
				billing_status = str(line.order_id.billing_state)

			sheet.write(y, x, billing_status , content1) #Billing Status
			x += 1


			x = 0
			y += 1
		for i in range(numbering):
			sheet.set_row(1+i, 60)