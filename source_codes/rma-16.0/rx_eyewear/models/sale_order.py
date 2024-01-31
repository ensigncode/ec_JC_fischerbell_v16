# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    optician_detail_id = fields.Many2one('optician.detail',string="Optician Detail")

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    child_id = fields.Many2one("res.partner",string="Employee name")