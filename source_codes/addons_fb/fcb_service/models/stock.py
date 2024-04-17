# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

class StockPicking(models.Model):
    _inherit = "stock.picking"


    def button_validate(self):
        res = super().button_validate()
        if self.picking_type_code != 'internal':
            line_ids = self.move_line_ids.filtered(lambda x: x.product_id.is_serviceable)
            equipment_services = self.env['equipment.service'].create(
                [{'product_id': line.product_id.id, 'lot_id': line.lot_id.id, 'delivered_qty': line.qty_done, 'partner_id': self.partner_id.id, 'delivered_date': self.date_done} for line in line_ids])
        return res
