from datetime import datetime
from odoo import models, tools

import io
import base64
import xlsxwriter
import mimetypes
import json

from odoo.tools.mimetypes import guess_mimetype

class FischerbellBillReport(models.AbstractModel):
	_name = 'report.fischerbell_custom.bill_report'
	_inherit = 'report.report_xlsx.abstract'



	def generate_xlsx_report(self, workbook, data, account_move):
		sheet = workbook.add_worksheet(account_move.name)
		sheet.set_landscape()
		numbering = 0
		link = 0


		sheet.set_row(0, 60)
		sheet.set_column('A:A', 5)
		sheet.set_column('B:B', 12)
		sheet.set_column('C:C', 12)
		sheet.set_column('D:D', 15)
		sheet.set_column('E:E', 10)
		sheet.set_column('F:F', 8)
		sheet.set_column('G:G', 15)
		sheet.set_column('H:H', 15)
		sheet.set_column('I:I', 10)
		sheet.set_column('J:J', 10)
		sheet.set_column('K:K', 14)
		sheet.set_column('L:L', 14)
		sheet.set_column('M:M', 12)
		sheet.set_column('N:N', 8)
		sheet.set_column('O:O', 12)
		sheet.set_column('P:P', 14)
		sheet.set_column('Q:Q', 10)
		sheet.set_column('R:R', 8)
		sheet.set_column('S:S', 8)
		sheet.set_column('T:T', 12)
		sheet.set_column('U:U', 12)
		sheet.set_column('V:V', 10)
		sheet.set_column('W:W', 10)

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
		sheet.write(y, x, 'Date', title2)
		x += 1
		sheet.write(y, x, 'Invoice Number', title2)
		x += 1
		sheet.write(y, x, 'Customer Code', title2)
		x += 1
		sheet.write(y, x, 'Customer Name', title2)
		x += 1
		sheet.write(y, x, 'Customer Reference No.', title2)
		x += 1
		sheet.write(y, x, 'Bill To', title2)
		x += 1
		sheet.write(y, x, 'Tel', title2)
		x += 1
		sheet.write(y, x, 'Fax Email', title2)
		x += 1
		sheet.write(y, x, 'Payment Terms', title2)
		x += 1
		sheet.write(y, x, 'Sales Rep', title2)
		x += 1
		sheet.write(y, x, 'SO Number', title2)
		x += 1
		sheet.write(y, x, 'DO Number', title2)
		x += 1
		sheet.write(y, x, 'Customers PO', title2)
		x += 1
		sheet.write(y, x, 'S/N', title2)
		x += 1
		sheet.write(y, x, 'SKU', title2)
		x += 1
		sheet.write(y, x, 'Description', title2)
		x += 1
		sheet.write(y, x, 'Quantity', title2)
		x += 1
		sheet.write(y, x, 'UOM', title2)
		x += 1
		sheet.write(y, x, 'Unit Price', title2)
		x += 1
		sheet.write(y, x, 'Amount $', title2)
		x += 1
		sheet.write(y, x, 'Subtotal $', title2)
		x += 1
		sheet.write(y, x, 'Tax 8%', title2)
		x += 1
		sheet.write(y, x, 'Total $', title2)
		x += 1

		x = 0
		y += 1
		for move in account_move:
			for line in move.invoice_line_ids:
				numbering += 1
				date = ''
				if line.move_id.invoice_date:
					date = line.move_id.invoice_date.strftime('%d %b %Y')
				sheet.write(y, x, date or '', content1) #Date
				x += 1
				sheet.write(y, x, line.move_id.name or '', content1) #Invoice Number
				x += 1
				sheet.write(y, x, line.move_id.partner_id.customer_code or '', content1) #Customer Code
				x += 1
				sheet.write(y, x, line.move_id.partner_id.name or '', content1) #Customer Name
				x += 1
				sheet.write(y, x, line.sale_ids.client_order_ref or '', content1) #Customer Ref No
				x += 1
				sheet.write(y, x, line.move_id.partner_id.name or '', content1) #Customer Bill To
				x += 1
				sheet.write(y, x, line.move_id.partner_id.phone or '', content1) #Tel
				x += 1
				fax_email = ''
				fax = ''
				email = ''
				if line.move_id.partner_id.fax:
					fax = line.move_id.partner_id.fax
				if line.move_id.partner_id.email:
					fax = line.move_id.partner_id.email

				fax_email = fax + ', ' + email
				sheet.write(y, x, fax_email, content1) #Fax Emal
				x += 1
				sheet.write(y, x, line.move_id.invoice_payment_term_id.name or '', content1) #Payment Term
				x += 1
				sheet.write(y, x, line.sale_ids.user_id.name or '', content1) #Sales Rep
				x += 1
				sheet.write(y, x, line.sale_ids.name or '', content1) #Sales Number
				x += 1
				do_number = ''
				for do in line.picking_ids:
					do_number += do.name + ', '
				sheet.write(y, x, do_number, content1) #DO Number
				x += 1
				sheet.write(y, x, line.move_id.purchase_order_id.name or '', content1) #Customers PO
				x += 1
				sheet.write(y, x, line.purchase_line_id.lot_id.name or '', content1) #S/N
				x += 1
				sheet.write(y, x, line.product_id.default_code or '', content1) #SKU
				x += 1
				sheet.write(y, x, line.name or '', content1) #Description
				x += 1
				sheet.write(y, x, line.quantity or '', content1) #Quantity
				x += 1
				sheet.write(y, x, line.product_uom_id.name or '', content1) #UOM
				x += 1
				sheet.write(y, x, line.price_unit or '', content1) #Unit Price
				x += 1
				sheet.write(y, x, line.price_unit or '', content1) #Amount
				x += 1
				sheet.write(y, x, line.price_subtotal or '', content1) #Subtotal
				x += 1
				tax_price = 0
				if line.tax_ids:
					for tax in line.tax_ids:
						tax_price = line.price_unit * (tax.amount / 100)
				sheet.write(y, x, tax_price or '', content1) #Tax 8%
				x += 1
				sheet.write(y, x, line.price_total or '', content1) #total
				x = 0
				y += 1

		for i in range(numbering):
			sheet.set_row(1+i, 60)