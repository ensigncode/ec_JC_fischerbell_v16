# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

class EquipmentService(models.Model):
    _name = "equipment.service"


    name = fields.Char(string="Service Type")
    partner_id = fields.Many2one('res.partner',string="Customer ")
    product_id = fields.Many2one('product.product',string="Product")
    delivered_date = fields.Datetime(string="Delivery Date")
