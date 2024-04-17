# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

class EquipmentService(models.Model):
    _name = "equipment.service"


    partner_id = fields.Many2one('res.partner',string="Customer ")
    product_id = fields.Many2one('product.product',string="Product")
    delivered_date = fields.Datetime(string="Delivery Date")
    lot_id = fields.Many2one('stock.lot',string="Lot/Serial Number")
    delivered_qty = fields.Float(string='Delivered Qty')
