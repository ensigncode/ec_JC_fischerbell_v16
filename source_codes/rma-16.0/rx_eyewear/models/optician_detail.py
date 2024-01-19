# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _

class OpticianDetail(models.Model):
    _name = 'optician.detail'

    name = fields.Char(string="Name")
    mobile = fields.Char(string="Mobile")
    product_id = fields.Many2one('product.template',string="Frame")
    group = fields.Char(string="Group")
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

    def create_sale_order(self) :

        sale_order_id = self.env['sale.order'].sudo().create({
            'optician_contact' : self.partner_id.id,
            'partner_id' : self.user_id.partner_id.id,
            'optician_detail_id' : self.id,
        })
        self.env['sale.order.line'].create({
                'name': _('Sample Order Line'),
                'product_id': self.product_id.id,
                'order_id': sale_order_id.id,
                'company_id': sale_order_id.company_id.id,
            })
        self.sale_order_id = sale_order_id.id