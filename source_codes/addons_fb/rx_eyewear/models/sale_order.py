# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
import json

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    optician_detail_id = fields.Many2one('optician.detail',string="Optician Detail")
    optician_detail_ids = fields.Many2many('optician.detail',string="Optician Detail")
    serial_number = fields.Char(string="Serial Number")

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
                            for move_id in sale_move_id :
                                child_id = move_id.sale_line_id.child_id.id if move_id.sale_line_id and move_id.sale_line_id.child_id else False
                                move_id.child_id = child_id

            move.child_id = child_id
        
class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    child_id = fields.Many2one("res.partner",string="Employee Id",related='move_id.child_id')
    lot_domain = fields.Char("Lot Domain", compute="_get_lot_domain")

    @api.depends("product_id")
    def _get_lot_domain(self):
        for line in self:
            if line.product_id.is_optic:
                stock_lot_ids = self.env['stock.lot'].search([('related_customer', '=', line.picking_id.partner_id.id)])
                lot_ids = [lot.id for lot in stock_lot_ids]
                if lot_ids:
                    line.lot_domain = json.dumps([('id', 'in', lot_ids)])
                else:
                    line.lot_domain = json.dumps([('id', 'in', [])])
            else:
                line.lot_domain = json.dumps([('product_id', '=', line.product_id.id), ('company_id', '=', line.company_id.id)])





    def _get_value_production_lot(self):
        res = super(StockMoveLine, self)._get_value_production_lot()
        if self.move_id.picking_id.purchase_id.sale_id.partner_id:
            res.update({
                'related_customer': self.move_id.picking_id.purchase_id.sale_id.partner_id.id
            })
        return res


class StockLot(models.Model):
    _inherit = 'stock.lot'

    related_customer = fields.Many2one('res.partner',string="Related Customer")