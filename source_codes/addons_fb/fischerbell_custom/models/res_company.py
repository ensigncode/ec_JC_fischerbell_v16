# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class Company(models.Model):
    _inherit = "res.company"

    social_lazada = fields.Char('Lazada Account')
    social_store = fields.Char('Woocommerce Account')
    social_shopee = fields.Char('Shopee Account')
    warehouse_id = fields.Many2one('stock.warehouse', string = 'Default Warehouse')
    picking_notification_days = fields.Integer()
