# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

class Task(models.Model):
    _inherit = "project.task"

    service_line = fields.One2many('service.order.line','service_id',string="Service Line")
    customer_code = fields.Char('Customer Code')
    customer_email = fields.Char('Email')


    @api.onchange('partner_id')
    def _onchange_partner(self):
        if self.partner_id:
            self.customer_code = self.partner_id.customer_code
        else:
            self.customer_code = False

class ServiceOrderLine(models.Model):
    _name = "service.order.line"


    product_temp_id = fields.Many2one('product.template', string='Product')
    service_id = fields.Many2one('project.task',string="Services")
    product_uom_qty = fields.Float(string="Quantity")
    price_unit = fields.Float(string="Unit Price")


class ServiceType(models.Model):
    _name = "service.type"

    name = fields.Char(string="Service Type")


