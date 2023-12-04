from datetime import datetime
from odoo import models, tools

import io
import base64
import xlsxwriter
import mimetypes
import json
from odoo.exceptions import UserError, ValidationError

from odoo.tools.mimetypes import guess_mimetype

class FischerbellOpenPoReport(models.AbstractModel):
	_name = 'report.fischerbell_custom.open_po_report'
	_inherit = 'report.report_xlsx.abstract'



	def generate_xlsx_report(self, workbook, data, stock_picking):
		sheet = workbook.add_worksheet('Open_PO_Report')
		sheet.set_landscape()
		numbering = 0
		link = 0


		sheet.set_row(0, 60)
		sheet.set_column('A:A', 5)
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
		sheet.set_column('P:P', 10)
		sheet.set_column('Q:Q', 8)
		sheet.set_column('R:R', 8)
		sheet.set_column('S:S', 8)
		sheet.set_column('T:T', 8)
		sheet.set_column('U:U', 8)
		sheet.set_column('V:V', 8)
		sheet.set_column('W:W', 8)
		sheet.set_column('X:X', 8)
		sheet.set_column('Y:Y', 8)

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
		sheet.write(y, x, 'Type of PO', title2)
		x += 1
		sheet.write(y, x, 'PO No', title2)
		x += 1
		sheet.write(y, x, 'PO Date', title2)
		x += 1
		sheet.write(y, x, 'Customer/Vendor Code', title2)
		x += 1
		sheet.write(y, x, 'Customer/Vendor Name', title2)
		x += 1
		sheet.write(y, x, 'Sales Employee Name', title2)
		x += 1
		sheet.write(y, x, 'Contact Person', title2)
		x += 1
		sheet.write(y, x, 'Telephone 1', title2)
		x += 1
		sheet.write(y, x, 'Row Number', title2)
		x += 1
		sheet.write(y, x, 'Item No', title2)
		x += 1
		sheet.write(y, x, 'Item/Service Description', title2)
		x += 1
		sheet.write(y, x, 'Quantity', title2)
		x += 1
		sheet.write(y, x, 'UOM', title2)
		x += 1
		sheet.write(y, x, 'Row Delivery Date', title2)
		x += 1
		sheet.write(y, x, 'Confirmation Date', title2)
		x += 1
		sheet.write(y, x, 'Remaining Open Quantity', title2)
		x += 1
		sheet.write(y, x, 'Price', title2)
		x += 1
		sheet.write(y, x, 'Price Currency', title2)
		x += 1
		sheet.write(y, x, 'Currency Rate', title2)
		x += 1
		sheet.write(y, x, 'Row Total', title2)
		x += 1
		sheet.write(y, x, 'Row Total FC', title2)
		x += 1
		sheet.write(y, x, 'Freight Charges', title2)
		x += 1
		sheet.write(y, x, 'Remarks', title2)
		x += 1
		sheet.write(y, x, 'Item Remarks', title2)
		x += 1
		sheet.write(y, x, 'Supplier (Local/Overseas)', title2)
		x += 1

		x = 0
		y += 1
		numbering = 0
		context = self.env.context
		for pick in stock_picking:
			if pick.picking_type_code != 'incoming':
				raise ValidationError("Sorry, the selected transfer is not receipt transfer.")
			else:
				list_pol = []
				for pol in pick.purchase_id.order_line:
					numbering += 1
					list_pol.append({'product': pol.product_id.id, 'row': numbering})

				for line in pick.move_ids_without_package:
					sheet.write(y, x, pick.po_type or '', content1) #Type of PO
					x += 1
					sheet.write(y, x, line.purchase_line_id.order_id.name, content1) #PO No
					x += 1

					po_date = ''
					if line.purchase_line_id.order_id.date_order:
						po_date = line.purchase_line_id.order_id.date_order.strftime('%d %b %Y')
					else:
						po_date = ''
					sheet.write(y, x, po_date, content1) #PO Date
					x += 1

					sheet.write(y, x, line.purchase_line_id.order_id.supplier_code or '', content1) #Customer/Vendor Code
					x += 1
					sheet.write(y, x, line.purchase_line_id.order_id.partner_id.name or '', content1) #Customer/Vendor Name
					x += 1
					sheet.write(y, x, line.purchase_line_id.order_id.partner_id.user_id.name or '', content1) #Sales Employee Name
					x += 1

					contact_person = ''
					telephone = ''
					for child in line.purchase_line_id.order_id.partner_id.child_ids:
						if child.type == 'contact':
							contact_person = child.name
							telephone = child.phone
						else:
							contact_person = ''
							telephone = ''
					sheet.write(y, x, contact_person, content1) #Contact Person
					x += 1

					sheet.write(y, x, telephone, content1) #Telephone 1
					x += 1
					for list_row in list_pol:
						product = list_row['product']
						row = list_row['row']
						if line.product_id.id == product:
							sheet.write(y, x, row, content1) #RowNumber
					x += 1
					sheet.write(y, x, line.product_id.default_code or '', content1) #Item No
					x += 1
					sheet.write(y, x, line.name, content1) #Item/Service Description
					x += 1
					if pick.state == 'done':
						sheet.write(y, x, '0', content1) #Quantity
						x += 1
					else:
						sheet.write(y, x, line.product_uom_qty, content1) #Quantity
						x += 1
					sheet.write(y, x, line.product_uom.name, content1) #UOM
					x += 1
					for receipt in line.purchase_line_id.order_id.picking_ids:
						if receipt.date_done:
							sheet.write(y, x, receipt.date_done.strftime('%d %b %Y'), content1) #Row Delivery Date
						else:
							sheet.write(y, x, '', content1) #Row Delivery Date
					x += 1

					confirm_date = ''
					if line.purchase_line_id.order_id.date_approve:
						confirm_date = line.purchase_line_id.order_id.date_approve.strftime('%d %b %Y')
					else:
						confirm_date = ''
					sheet.write(y, x, confirm_date, content1) #Confirmation Date
					x += 1
					moves = [
					    move
					    for picking in line.purchase_line_id.order_id.picking_ids
					    if picking.state not in ('cancel', 'done')
					    for move in picking.move_ids_without_package
					    if move.product_id == line.product_id
					]

					for move in moves:
					    sheet.write(y, x, move.product_uom_qty, content1)  # Remaining Open Quantity
					x += 1
					sheet.write(y, x, line.purchase_line_id.price_unit, content1) #Price
					x += 1
					sheet.write(y, x, line.purchase_line_id.currency_id.name, content1) #Currency
					x += 1
					sheet.write(y, x, line.purchase_line_id.currency_id.rate, content1) #Currency Rate
					x += 1

					row_total = []
					row_total_fc = []
					for po_line in pick.move_ids_without_package:
						if po_line.purchase_line_id.currency_id != line.purchase_line_id.company_id.currency_id:
							row_total.append(po_line.id)
						if po_line.purchase_line_id.currency_id == line.purchase_line_id.company_id.currency_id:
							row_total_fc.append(po_line.id)
					if len(row_total) > 0:
						sheet.write(y, x, len(row_total), content1)
						x += 1
					else:
						sheet.write(y, x, '', content1)
						x += 1

					if len(row_total_fc) > 0:
						sheet.write(y, x, len(row_total_fc), content1)
						x += 1
					else:
						sheet.write(y, x, '', content1)
						x += 1

					freight_charge = ''
					bill_name = ''
					for bill in line.purchase_line_id.order_id.invoice_ids:
						bill_name = bill.name
					freight_charges = self.env['account.move'].search([('ref','=',bill_name)])
					for fc in freight_charges.move_ids:
						for fc_line in fc.invoice_line_ids:
							if fc_line.product_id.id == line.product_id.id:
								freight_charge = fc_line.price_unit
							else:
								freight_charge = ''

					sheet.write(y, x, freight_charge, content1) #Freight Charges
					x += 1

					if line.purchase_line_id.order_id.internal_note:
						sheet.write(y, x, line.purchase_line_id.order_id.internal_note, content1) #Remarks
						x += 1
					else:
						sheet.write(y, x, '', content1) #Remarks
						x += 1

					if line.product_id.description:
						sheet.write(y, x, line.product_id.description, content1)
						x += 1
					else:
						sheet.write(y, x, '', content1)
						x += 1

					if line.purchase_line_id.order_id.partner_id.currency_type:
						sheet.write(y, x, line.purchase_line_id.order_id.partner_id.currency_type, content1) #Supplier (Local/Overseas)
						x += 1
					else:
						sheet.write(y, x, line.purchase_line_id.order_id.partner_id.currency_type or '', content1) #Supplier (Local/Overseas)
						x += 1


					x = 0
					y += 1
		for i in range(numbering):
			sheet.set_row(1+i, 60)