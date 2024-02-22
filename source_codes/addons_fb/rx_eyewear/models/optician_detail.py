# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from io import BytesIO
import xlwt
import base64
from odoo.tools.misc import xlsxwriter

class OpticianDetail(models.Model):
    _name = 'optician.detail'

    name = fields.Char(string="Employee Name")
    mobile = fields.Char(string="Mobile")
    email = fields.Char(string="Email")
    emp_no = fields.Char(string="NRIC / FIN No. / Employee No.")
    dept_code = fields.Char(string="Department code")
    lens_type = fields.Char(string="Lens Type")
    presc_type = fields.Char(string="Type of Prescription")
    add_on_type = fields.Char(string="Add on type")
    product_id = fields.Many2one('product.template',string="Frame", domain = "[('is_optic', '=', True)]")
    company_id = fields.Many2one('res.partner',string="Company", domain = "[('is_company', '=', True)]")
    sphere_left = fields.Char(string="SPHERE LEFT")
    cyl_left = fields.Char(string="CYL LEFT")
    axis_left = fields.Char(string="AXIS LEFT")
    sphere_right = fields.Char(string="SPHERE RIGHT")
    cyl_right = fields.Char(string="CYL RIGHT")
    axis_right = fields.Char(string="AXIS RIGHT")
    add = fields.Char(string="ADD")
    pd = fields.Char(string="PD")
    requirements = fields.Text(string="REQUIRMENTS")
    user_id = fields.Many2one('res.users',string="User")
    partner_id = fields.Many2one("res.partner",string="Partner")
    sale_order_id = fields.Many2one("sale.order",string="Sale Order")
    sale_order_ids = fields.One2many("sale.order","optician_detail_id",string="Sale Order")
    sale_order_count = fields.Integer(string="Sale Order",compute="_compute_sale_order_count")

    @api.depends('sale_order_ids')
    def _compute_sale_order_count(self):
        for record in self:
            record.sale_order_count = len(record.sale_order_ids)


    def action_show_sale_order(self):
        self.ensure_one()
        sale_order_ids = self.sale_order_ids
        result = self.env['ir.actions.act_window']._for_xml_id('sale.action_orders')
        if len(sale_order_ids) > 1:
            result['domain'] = [('id', 'in', sale_order_ids.ids)]
        elif len(sale_order_ids) == 1:
            result['views'] = [(self.env.ref('sale.view_order_form', False).id, 'form')]
            result['res_id'] = sale_order_ids.id
        return result
        
                

    def action_create_quotation(self):
        company_partner_ids = self.mapped("company_id")
        sale_order_ids = []
        for company in company_partner_ids :
            filtered_records = self.filtered(lambda l: l.company_id.id == company.id)
            
            sale_order_id = self.env['sale.order'].sudo().create({
                'partner_id' : company.id,
                'optician_detail_id':self.id,
            })
            for filter_rec in filtered_records :
                new_line = self.env['sale.order.line'].sudo().create({
                    # 'name': filter_rec.product_id.product_variant_id.description,
                    'child_id' : filter_rec.partner_id.id,
                    'child_name' : filter_rec.partner_id.display_name,
                    'product_id': filter_rec.product_id.product_variant_id.id,
                    'order_id': sale_order_id.id,
                    'product_uom_qty': 1,
                    'price_unit': filter_rec.product_id.product_variant_id.list_price,
                    "product_uom" : filter_rec.product_id.product_variant_id.uom_id.id,
                })
           

class FischerbellOpticianDetailReport(models.AbstractModel):
    _name = 'report.rx_eyewear.optician_detail_report'
    _inherit = 'report.report_xlsx.abstract'

    
    def generate_xlsx_report(self, workbook, data, optician_details):
        sheet = workbook.add_worksheet('Optician Detail')
        sheet.set_row(0, 60)
        content1 = workbook.add_format()
        content1.set_bold()
        content1.set_font_size(10)
        content1.set_align('center')
        content1.set_align('Arial')
        content1.set_text_wrap()
        content1.set_font_color('#000000')
        content1.set_bg_color('#C0C0C0')
        content1.set_border(1)

        content2 = workbook.add_format()
        content2.set_font_size(8)
        content2.set_text_wrap()
        content2.set_align('left')
        content2.set_align('vcenter')
        content2.set_align('Arial')

        sheet.set_column('A:A', 25)
        sheet.set_column('B:B', 25)
        sheet.set_column('C:C', 35)
        sheet.set_column('D:D', 15)
        sheet.set_column('E:E', 15)
        sheet.set_column('F:F', 15)
        sheet.set_column('G:G', 20)
        sheet.set_column('P:P', 20)
        sheet.set_column('Q:Q', 20)
        sheet.set_column('R:R', 20)
        sheet.set_column('S:S', 20)

        sheet.write(0, 0, 'Name', content1)
        sheet.write(0, 1, 'Group', content1)
        sheet.write(0, 2, 'FRAME',content1)
        sheet.write(0, 3 , 'NRIC / FIN No. / Employee No.', content1)
        sheet.write(0, 4 , 'DEPARTMENT CODE', content1)
        sheet.write(0, 5, 'MOBILE',content1)
        sheet.write(0, 6, 'Email',content1)
        sheet.write(0, 7, 'SPHERE RIGHT',content1)
        sheet.write(0, 8, 'CYL RIGHT',content1)
        sheet.write(0, 9, 'AXIS RIGHT',content1)
        sheet.write(0, 10, 'SPHERE LEFT',content1)
        sheet.write(0, 11, 'CYL LEFT',content1)
        sheet.write(0, 12, 'AXIS LEFT',content1)
        sheet.write(0, 13, 'ADD',content1)
        sheet.write(0, 14, 'PD',content1)
        sheet.write(0, 15, 'REQUIREMENTS',content1)
        sheet.write(0, 16, 'Type of Lens',content1)
        sheet.write(0, 17, 'Type of Prescription',content1)
        sheet.write(0, 18, 'Add on',content1)


        x = 0
        y = 1
        sheet.set_row(y, 30)
        for optician_detail in optician_details :
            sheet.write(y, x, optician_detail.name or '', content2) 
            x += 1
            sheet.write(y, x, optician_detail.company_id.name or '', content2)
            x += 1
            sheet.write(y, x, optician_detail.product_id.name or '', content2)
            x += 1
            sheet.write(y, x, optician_detail.emp_no or '', content2)
            x += 1
            sheet.write(y, x, optician_detail.dept_code or '', content2)
            x += 1
            sheet.write(y, x, optician_detail.mobile or '', content2)
            x += 1
            sheet.write(y, x, optician_detail.email or '', content2)
            x += 1
            sheet.write(y, x, optician_detail.sphere_right or '', content2)
            x += 1
            sheet.write(y, x, optician_detail.cyl_right or '', content2)
            x += 1
            sheet.write(y, x, optician_detail.axis_right or '', content2)
            x += 1
            sheet.write(y, x, optician_detail.sphere_left or '', content2)
            x += 1
            sheet.write(y, x, optician_detail.cyl_left or '', content2)
            x += 1
            sheet.write(y, x, optician_detail.axis_left or '', content2)
            x += 1
            sheet.write(y, x, optician_detail.add or '', content2)
            x += 1
            sheet.write(y, x, optician_detail.pd or '', content2)
            x += 1
            sheet.write(y, x, optician_detail.requirements or '', content2)
            x += 1
            sheet.write(y, x, optician_detail.lens_type or '', content2)
            x += 1
            sheet.write(y, x, optician_detail.presc_type or '', content2)
            x += 1
            sheet.write(y, x, optician_detail.add_on_type or '', content2)


            x = 0
            y += 1
            sheet.set_row(y, 30)
