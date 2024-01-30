# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _

class OpticianDetail(models.Model):
    _name = 'optician.detail'

    name = fields.Char(string="Name")
    mobile = fields.Char(string="Mobile")
    email = fields.Char(string="Email")
    emp_no = fields.Char(string="NRIC / FIN No. / Employee No.")
    dept_code = fields.Char(string="Department code")
    lens_type = fields.Char(string="Lens Type")
    presc_type = fields.Char(string="Type of Prescription")
    add_on_type = fields.Char(string="Add on type")
    product_id = fields.Many2one('product.template',string="Frame", domain = "[('is_optic', '=', True)]")
    company_id = fields.Many2one('res.partner',string="Group", domain = "[('is_company', '=', True)]")
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

    
    def action_create_quotation(self):
        company_partner_ids = self.mapped("company_id")
        sale_order_ids = []
        for company in company_partner_ids :
            filtered_records = self.filtered(lambda l: l.company_id.id == company.id)
            
            sale_order_id = self.env['sale.order'].sudo().create({
                'partner_id' : company.id,
            })
            for filter_rec in filtered_records :
                new_line = self.env['sale.order.line'].sudo().create({
                    'name': _('Sample Order Line'),
                    'child_id' : filter_rec.partner_id.id,
                    'product_id': filter_rec.product_id.product_variant_id.id,
                    'order_id': sale_order_id.id,
                    'product_uom_qty': 1,
                    'price_unit': filter_rec.product_id.product_variant_id.list_price,
                    "product_uom" : filter_rec.product_id.product_variant_id.uom_id.id,
                })
            sale_order_ids.append(sale_order_id.id)
        view_id_list = self.env.ref('sale.view_quotation_tree').id
        view_id_form = self.env.ref('sale.view_order_form').id
        return {
            'name': 'Sale Orders',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'tree,form',
            'views': [[view_id_list, 'list'], [view_id_form, 'form']],
            'view_id': self.env.ref('sale.view_quotation_tree').id,  # Adjust the view_id based on your Sale Order tree view
            'domain': [('id','in',sale_order_ids)],
        }
                