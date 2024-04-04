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

    child_id = fields.Many2one("res.partner",string="Employee Id",compute="compute_employee")

    def compute_employee(self):
        child_id = False
        for move in self:
            if move.picking_id and move.picking_id.sale_id:
                sale_id = move.picking_id.sale_id
                all_picking_ids = sale_id.picking_ids
                moves = all_picking_ids.mapped('move_ids_without_package')
                sale_moves = moves.filtered(lambda x:x.sale_line_id)
                if sale_moves :
                    for sale_move in sale_moves:
                        child_id = move.sale_line_id.child_id.id if move.sale_line_id and move.sale_line_id.child_id else False

                    rem_moves = moves.filtered(lambda x:x.id not in sale_moves.ids)
                    if rem_moves :
                        for rem_move in rem_moves:
                            sale_move_id = sale_moves.filtered(lambda x:x.product_id.id == rem_move.product_id.id)
                            child_id = sale_move_id.sale_line_id.child_id.id if sale_move_id.sale_line_id and sale_move_id.sale_line_id.child_id else False

            move.child_id = child_id
        
class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    child_id = fields.Many2one("res.partner",string="Employee Id",related='move_id.child_id')