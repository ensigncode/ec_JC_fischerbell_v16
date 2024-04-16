# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

class StockPicking(models.Model):
    _inherit = "stock.picking"


    def button_validate(self):
        res = super().button_validate()
        product_ids = self.move_line_ids.filtered(lambda x: x.product_id.is_serviceable).mapped('product_id')
        equipment_services = self.env['equipment.service'].create(
            [{'product_id': prod.id, 'partner_id': self.partner_id.id, 'delivered_date': self.date_done} for prod in product_ids])
        return res
