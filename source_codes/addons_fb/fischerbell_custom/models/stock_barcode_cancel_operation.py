# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class StockBarcodeCancelPicking(models.TransientModel):
    _inherit = 'stock_barcode.cancel.operation'

    reason_id = fields.Many2one('stock.barcode.cancel.reason', string="Cancelation Reason")

    def action_cancel_operation(self):
        res = self.picking_id.action_cancel()
        self.picking_id.message_post(body=self.reason_id.name, subject="DO Cancelled")
        return {'type': 'ir.actions.act_window_close', 'infos': {'cancelled': res}}


class StockBarcodeCancelReasons(models.Model):
    _name = "stock.barcode.cancel.reason"
    _description = "StockBarcodeCancelReason"

    name = fields.Char(string="Cancel Reason")
