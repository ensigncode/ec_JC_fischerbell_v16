# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    optician_detail_id = fields.Many2one('optician.detail',string="Optician Detail")

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    child_id = fields.Many2one("res.partner",string="Employee id")
    child_name = fields.Char("Employee name")

class StockMove(models.Model):
    _inherit = 'stock.move'

    child_id = fields.Many2one("res.partner",string="Employee Id",compute="compute_child_id")

    def compute_child_id(self):
        if self.picking_id and self.picking_id.sale_id:

            sale_id = self.picking_id.sale_id
            all_picking_ids = sale_id.picking_ids

            moves = all_picking_ids.mapped('move_ids_without_package')
            sale_moves = moves.filtered(lambda x:x.sale_line_id)

            for move in sale_moves:
                move.child_id = move.sale_line_id.child_id.id

            rem_moves = moves.filtered(lambda x:x.id not in sale_moves.ids)
            for move in rem_moves:
                sale_move_id = sale_moves.filtered(lambda x:x.product_id.id == move.product_id.id)
                move.child_id = sale_move_id.sale_line_id.child_id.id
        else :
            self.child_id = False
        
class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    child_id = fields.Many2one("res.partner",string="Employee Id",related='move_id.child_id')