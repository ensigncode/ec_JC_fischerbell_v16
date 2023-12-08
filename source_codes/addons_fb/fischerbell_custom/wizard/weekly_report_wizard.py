import base64
import calendar

from odoo import _, api, models, fields
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Border, Side, Alignment, Font
from io import BytesIO


class WeeklyReportwizard(models.TransientModel):
    _name = "weekly.report.wizard"
    _description = "Weekly Report Wizard"

    years = {'2015':'2015'}

    def _get_years(self):
        last = max(self.years.keys())
        current = datetime.now().year
        if int(last) < current:
            self.years.update(dict([[str(i),str(i)] for i in range(int(last)+1,current+1)]))
        return [(year,year) for year in self.years]

    year = fields.Selection(_get_years,"Year", required=True)


    def action_create_weekly_report(self):
        wb = Workbook()
        f_name = 'Quotation Report'

        table_header_alignment = Alignment(horizontal='left', vertical='top', text_rotation=0, wrap_text=True)
        bold_text = Font(name="Calibri", size=11, bold=True)
        border_bottom = Border(bottom=Side(style='thin'))

        order_ids = [x  for x in self.env['sale.order'].search([]) if x.date_order.year == eval(self.year)]
        
        table_header = 1

        for month in range(1,13):
            wrksht = wb.create_sheet(title=calendar.month_name[month])
            table_row = table_header + 1
            table_col = 1

            wrksht.cell(row=table_header, column=1).value = 'Date'
            wrksht.cell(row=table_header, column=1).font = bold_text
            wrksht.cell(row=table_header, column=1).alignment = table_header_alignment
            wrksht.cell(row=table_header, column=1).border = border_bottom

            wrksht.cell(row=table_header, column=2).value = 'Company'
            wrksht.cell(row=table_header, column=2).font = bold_text
            wrksht.cell(row=table_header, column=2).alignment = table_header_alignment
            wrksht.cell(row=table_header, column=2).border = border_bottom

            wrksht.cell(row=table_header, column=3).value = 'Contact'
            wrksht.cell(row=table_header, column=3).font = bold_text
            wrksht.cell(row=table_header, column=3).alignment = table_header_alignment
            wrksht.cell(row=table_header, column=3).border = border_bottom

            wrksht.cell(row=table_header, column=4).value = 'Salesperson'
            wrksht.cell(row=table_header, column=4).font = bold_text
            wrksht.cell(row=table_header, column=4).alignment = table_header_alignment
            wrksht.cell(row=table_header, column=4).border = border_bottom

            wrksht.cell(row=table_header, column=5).value = 'Quotation SQ no.'
            wrksht.cell(row=table_header, column=5).font = bold_text
            wrksht.cell(row=table_header, column=5).alignment = table_header_alignment
            wrksht.cell(row=table_header, column=5).border = border_bottom

            wrksht.cell(row=table_header, column=6).value = 'Revision SQ no.'
            wrksht.cell(row=table_header, column=6).font = bold_text
            wrksht.cell(row=table_header, column=6).alignment = table_header_alignment
            wrksht.cell(row=table_header, column=6).border = border_bottom

            wrksht.cell(row=table_header, column=7).value = 'Processor'
            wrksht.cell(row=table_header, column=7).font = bold_text
            wrksht.cell(row=table_header, column=7).alignment = table_header_alignment
            wrksht.cell(row=table_header, column=7).border = border_bottom

            wrksht.cell(row=table_header, column=8).value = 'Quote by'
            wrksht.cell(row=table_header, column=8).font = bold_text
            wrksht.cell(row=table_header, column=8).alignment = table_header_alignment
            wrksht.cell(row=table_header, column=8).border = border_bottom
        
            wrksht.cell(row=table_header, column=9).value = 'Review by'
            wrksht.cell(row=table_header, column=9).font = bold_text
            wrksht.cell(row=table_header, column=9).alignment = table_header_alignment
            wrksht.cell(row=table_header, column=9).border = border_bottom

            wrksht.cell(row=table_header, column=10).value = 'Email date'
            wrksht.cell(row=table_header, column=10).font = bold_text
            wrksht.cell(row=table_header, column=10).alignment = table_header_alignment
            wrksht.cell(row=table_header, column=10).border = border_bottom

            wrksht.cell(row=table_header, column=11).value = 'Follow Up'
            wrksht.cell(row=table_header, column=11).font = bold_text
            wrksht.cell(row=table_header, column=11).alignment = table_header_alignment
            wrksht.cell(row=table_header, column=11).border = border_bottom

            wrksht.cell(row=table_header, column=12).value = '2nd Follow Up'
            wrksht.cell(row=table_header, column=12).font = bold_text
            wrksht.cell(row=table_header, column=12).alignment = table_header_alignment
            wrksht.cell(row=table_header, column=12).border = border_bottom

            wrksht.cell(row=table_header, column=13).value = 'Status'
            wrksht.cell(row=table_header, column=13).font = bold_text
            wrksht.cell(row=table_header, column=13).alignment = table_header_alignment
            wrksht.cell(row=table_header, column=13).border = border_bottom

            wrksht.cell(row=table_header, column=14).value = 'Win / Lost / Pending'
            wrksht.cell(row=table_header, column=14).font = bold_text
            wrksht.cell(row=table_header, column=14).alignment = table_header_alignment
            wrksht.cell(row=table_header, column=14).border = border_bottom

            wrksht.cell(row=table_header, column=15).value = 'Reason for Lost'
            wrksht.cell(row=table_header, column=15).font = bold_text
            wrksht.cell(row=table_header, column=15).alignment = table_header_alignment
            wrksht.cell(row=table_header, column=15).border = border_bottom

            for order in filter(lambda ord:ord.date_order.month == month,order_ids):
                
                wrksht.cell(row=table_row, column=table_col).value = order.date_order.date() if order.date_order else ''
                wrksht.cell(row=table_row, column=table_col).alignment = table_header_alignment

                wrksht.cell(row=table_row, column=table_col+1).value = order.contact_person_id.parent_id.name or ''
                wrksht.cell(row=table_row, column=table_col+1).alignment = table_header_alignment

                wrksht.cell(row=table_row, column=table_col+2).value = order.contact_person_id.name or ''
                wrksht.cell(row=table_row, column=table_col+2).alignment = table_header_alignment

                wrksht.cell(row=table_row, column=table_col+3).value = order.user_id.name or ''
                wrksht.cell(row=table_row, column=table_col+3).alignment = table_header_alignment

                wrksht.cell(row=table_row, column=table_col+4).value = order.name or ''
                wrksht.cell(row=table_row, column=table_col+4).alignment = table_header_alignment

                wrksht.cell(row=table_row, column=table_col+5).value = order.revision_order_name or ''
                wrksht.cell(row=table_row, column=table_col+5).alignment = table_header_alignment

                wrksht.cell(row=table_row, column=table_col+6).value = order.team_id.name or ''
                wrksht.cell(row=table_row, column=table_col+6).alignment = table_header_alignment

                wrksht.cell(row=table_row, column=table_col+7).value = order.reviewed_by.name or ''
                wrksht.cell(row=table_row, column=table_col+7).alignment = table_header_alignment

                wrksht.cell(row=table_row, column=table_col+8).value = order.write_uid.name or ''
                wrksht.cell(row=table_row, column=table_col+8).alignment = table_header_alignment

                wrksht.cell(row=table_row, column=table_col+9).value = order.email_to_customer or ''
                wrksht.cell(row=table_row, column=table_col+9).alignment = table_header_alignment

                wrksht.cell(row=table_row, column=table_col+10).value = order.first_followup_date.date() if order.first_followup_date else ''
                wrksht.cell(row=table_row, column=table_col+10).alignment = table_header_alignment

                wrksht.cell(row=table_row, column=table_col+11).value = order.sec_followup_date.date() if order.sec_followup_date else ''
                wrksht.cell(row=table_row, column=table_col+11).alignment = table_header_alignment

                wrksht.cell(row=table_row, column=table_col+12).value = dict(order._fields['state'].selection).get(order.state) or ''
                wrksht.cell(row=table_row, column=table_col+12).alignment = table_header_alignment

                wrksht.cell(row=table_row, column=table_col+13).value = order.opportunity_id.stage_id.name == '' or ''
                wrksht.cell(row=table_row, column=table_col+13).alignment = table_header_alignment

                wrksht.cell(row=table_row, column=table_col+14).value = order.opportunity_id.lost_reason_id.name or ''
                wrksht.cell(row=table_row, column=table_col+14).alignment = table_header_alignment

                 
                wrksht.column_dimensions['A'].width = 16
                wrksht.column_dimensions['B'].width = 14
                wrksht.column_dimensions['C'].width = 14
                wrksht.column_dimensions['D'].width = 14
                wrksht.column_dimensions['E'].width = 14
                wrksht.column_dimensions['F'].width = 14
                wrksht.column_dimensions['G'].width = 14
                wrksht.column_dimensions['H'].width = 14
                wrksht.column_dimensions['I'].width = 14
                wrksht.column_dimensions['J'].width = 16
                wrksht.column_dimensions['K'].width = 16
                wrksht.column_dimensions['L'].width = 16
                wrksht.column_dimensions['M'].width = 14
                wrksht.column_dimensions['N'].width = 14
                wrksht.column_dimensions['O'].width = 14

                table_row += 1

        wb.remove(wb.active)

        fp = BytesIO()
        wb.save(fp)
        fp.seek(0)
        data = fp.read()
        fp.close()

        wiz_id = self.env['download.report.wizard'].create({'file':base64.b64encode(data)})


        return {
            'type': 'ir.actions.act_url',
            'url': 'web/content/?model=download.report.wizard&download=true&field=file&id=%s&filename=%s.xlsx' % (wiz_id.id, f_name),
            'target': 'self',
        }
