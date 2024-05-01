from odoo import _, api, fields, models
from datetime import timedelta, datetime
from odoo.exceptions import UserError
import logging
from datetime import datetime, timedelta, date

_logger = logging.getLogger(__name__)

try:
    import xlsxwriter
    from xlsxwriter.utility import xl_range
except ImportError:
    _logger.debug('Cannot `import xlsxwriter`.')
try:
    import base64
except ImportError:
    _logger.debug('Cannot `import base64`.')

class LandCostWizard(models.TransientModel):
    _name = 'land.cost.report.wizard'
    _description = 'Land Cost Report Wizard'

    document = fields.Binary('Files To Download')
    file = fields.Char('Report File Name', readonly=1)

    def action_create_cost_analysis_report(self):
        print("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")

        context = dict(self._context or {})
        file_path = 'Product_Purchase' + '.xlsx'
        workbook = xlsxwriter.Workbook('/tmp/' + file_path)

        header_table_format = workbook.add_format(
            {'border': 1, 'bold': True, 'valign': 'vcenter', 'align': 'center', 'font_size': 11})
        cell_wrap_format = workbook.add_format(
            {'valign': 'vjustify', 'valign': 'vcenter', 'align': 'center', 'font_size': 11})
        cell_number_format = workbook.add_format(
            {'valign': 'vjustify', 'valign': 'vcenter', 'align': 'center', 'font_size': 11})
        cell_float_format = workbook.add_format(
            {'num_format': '#,##0.00', 'valign': 'vjustify', 'valign': 'vcenter', 'align': 'center', 'font_size': 11})
        header_table_format.set_text_wrap()

        worksheet = workbook.add_worksheet('')
        worksheet.set_row(1,20)
        worksheet.set_column(0, 0, 30)
        worksheet.set_column(1, 1, 70)
        worksheet.set_column(2, 2, 15)
        worksheet.set_column(3, 3, 15)
        worksheet.set_column(4, 4, 70)
        worksheet.set_column(5, 5, 15)
        worksheet.set_column(6, 6, 15)
        worksheet.set_column(7, 7, 15)
        worksheet.set_column(8, 8, 60)
        worksheet.set_column(9, 9, 60)

        # Report Title
        worksheet.merge_range(0, 0, 0, 8, 'Landed Cost Report', header_table_format)
        worksheet.write(3, 0, 'Item No.', header_table_format)
        worksheet.write(3, 1, 'Description', header_table_format)
        worksheet.write(3, 2, 'UoM Name', header_table_format)
        worksheet.write(3, 3, 'Qty', header_table_format)
        worksheet.write(3, 4, 'Landed Cost Item Price', header_table_format)
        worksheet.write(3, 5, 'Base Doc. Price', header_table_format)
        worksheet.write(3, 6, 'Freight (FC)', header_table_format)
        worksheet.write(3, 7, 'Item Price (FC)', header_table_format)
        worksheet.write(3, 8, 'Exchange Rate', header_table_format)

        rows = 5

        purchase_ids = self.env['purchase.order'].sudo().browse(443)
        print("---purchase_ids--------",purchase_ids)
        for purchase_id in purchase_ids:
            rate_ids = purchase_id.currency_id.mapped('rate_ids')
            if rate_ids:
                company_rate_id = rate_ids[0]
                currency_id= company_rate_id.company_rate
            else:
                currency_id = 1
            for line in purchase_id.order_line:
                invoices = line.mapped('invoice_lines.move_id')
                if invoices:
                    for invoice in invoices:
                        move_ids = list(filter(lambda x: (
                            x.move_type == 'in_invoice' and x.account_move_id == invoice.id and x.is_freight_charge == True,
                            x.ref == invoice.name), invoice.move_ids))
                        print("-------move_ids",move_ids)
                        for move_id in move_ids:
                            invoice_line_ids = move_id.invoice_line_ids
                            for invoice_line_id in invoice_line_ids:
                                freight_price = invoice_line_id.price_unit
                                currency_and_price = f"{line.order_id.currency_id.name} { line.price_unit}"
                                item_price = line.price_unit + freight_price
                                cost = (line.product_qty * line.price_unit / purchase_id.amount_total) if purchase_id.amount_total != 0 else 0
                                print("---cost-------",cost)
                                landed_cost = round((freight_price * cost) + line.price_unit, 2)
                                print("=-landed_cost-----",landed_cost)
                                company_currency_name = line.company_id.currency_id.name
                                purchase_order_currency = purchase_id.currency_id.name
                                landed_cost_with_currency = f"{company_currency_name} {landed_cost}"
                                print("---------landed_cost_with_currency,landed_cost_with_currency",landed_cost_with_currency)
                                fright_purchase_order_cu = f"{purchase_order_currency} {freight_price}"
                                print("------------fright_purchase_order_cu",fright_purchase_order_cu)
                                item_purchase_order_cu = f"{purchase_order_currency} {item_price}"
                                print("-------------------item_purchase_order_cu",item_purchase_order_cu)
                                worksheet.write(rows, 0, line.product_id.default_code if line.product_id.default_code else '',
                                                cell_wrap_format)
                                worksheet.write(rows, 1, line.product_id.name, cell_wrap_format)
                                worksheet.write(rows, 2, line.product_uom.name, cell_wrap_format)
                                worksheet.write(rows, 3, line.product_uom_qty, cell_float_format)
                                worksheet.write(rows, 4, landed_cost_with_currency or 0, cell_wrap_format)
                                worksheet.write(rows, 5, currency_and_price or 0, cell_float_format)
                                worksheet.write(rows, 6, fright_purchase_order_cu or 0, cell_float_format)
                                worksheet.write(rows, 7, item_purchase_order_cu or 0 ,cell_wrap_format)
                                worksheet.write(rows, 8, currency_id, cell_wrap_format),

                                rows += 1
                else:
                    landed_cost = round( line.price_unit, 2)
                    purchase_order_currency = purchase_id.currency_id.name
                    company_currency_name = line.company_id.currency_id.name
                    landed_cost_with_currency = f"{company_currency_name} {landed_cost}"
                    print("-1-------------landed_cost_with_currency",landed_cost_with_currency)
                    currency_and_price = f"{line.order_id.currency_id.name} {line.price_unit}"
                    print("-2----currency_and_price-----",currency_and_price)
                    item_price = line.price_unit
                    item_purchase_order_cu = f"{purchase_order_currency} {item_price}"
                    print("3---------------item_purchase_order_cu",item_purchase_order_cu)
                    worksheet.write(rows, 0, line.product_id.default_code if line.product_id.default_code else '',
                                    cell_wrap_format)
                    worksheet.write(rows, 1, line.product_id.name, cell_wrap_format)
                    worksheet.write(rows, 2, line.product_uom.name, cell_wrap_format)
                    worksheet.write(rows, 3, line.product_uom_qty, cell_float_format)
                    worksheet.write(rows, 4, landed_cost_with_currency or 0, cell_wrap_format)
                    worksheet.write(rows, 5, currency_and_price or 0, cell_float_format)
                    worksheet.write(rows, 6,  0, cell_float_format)
                    worksheet.write(rows, 7, item_purchase_order_cu or 0, cell_wrap_format)
                    worksheet.write(rows, 8, currency_id, cell_wrap_format),

                    rows += 1

        workbook.close()
        buf = base64.b64encode(open('/tmp/' + file_path, 'rb+').read())
        self.document = buf
        self.file = 'Product_Purchase' + '.xlsx'

        return {
            'res_id': self.id,
            'name': 'Product Purchase',
            'view_type': 'form',
            "view_mode": 'form',
            'res_model': 'land.cost.report.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
        }


