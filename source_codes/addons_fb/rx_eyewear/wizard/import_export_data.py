# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from xlrd import open_workbook
import base64
import xlsxwriter
import datetime
import math
import logging
_logger = logging.getLogger(__name__)

class ImportExportData(models.Model):
    _name = 'eyewear.import.export.data'
    _description = 'EyeWear Import Export Data'

    name = fields.Char(string='Name')
    choose_file = fields.Binary('Choose File')
    filename = fields.Char('filename')

    def print_report_excel_data(self):
        self.ensure_one()
        file_name = '/tmp/rx_eyewear_template.xlsx'
        workbook = xlsxwriter.Workbook(file_name, {'constant_memory': True})
        sheet = workbook.add_worksheet('rx_eyewear_template')
        sheet.freeze_panes(1, 0)
        sheet.set_row(0, 20)

        cell = workbook.add_format()
        cell.set_bold()
        cell.set_font_size(12)
        cell.set_align('center')
        cell.set_align('vcenter')
        cell.set_text_wrap()

        note_format = workbook.add_format({
            'bold': True,
            'font_color': 'red',
            'font_size': 12,
            'align': 'center',
            'valign': 'vcenter',
            'text_wrap': True
        })

        term_condition = self.env['optician.term.condition'].search([], limit=1)

        header_list = ["User", "Employee Name", "Mobile", "Email", "NRIC / FIN No. / Employee No", "Department code", "Lens Type",  "Add on type", "Frame", "Company", "SPHERE LEFT", "CYL LEFT", "AXIS LEFT", "SPHERE RIGHT", "CYL RIGHT", "AXIS RIGHT", "ADD", "PD", "REQUIRMENTS", "SG HT", "Prescription", "Outlet", "ADD RIGHT", "ADD LEFT", "PD RIGHT", "PD LEFT", "Terms And Conditions"]
        col = 0
        for header in header_list:
            sheet.write(0, col, header, cell)
            if len(header) > 7:
                sheet.set_column(col, col, len(header)+5)
            if col == 26:
                sheet.write(1, col, term_condition.name, note_format)
            col += 1

        count_paid = 1
        max_width_product = 0
        sheet.set_column(1, 1, max_width_product)
        workbook.close()
        with open(file_name, "rb") as file:
            data = file.read()
            return base64.b64encode(data)


    def export_order_line(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/binary/download_document/rx_eyewear/%s' % self.id,
            'target': 'self',
        }