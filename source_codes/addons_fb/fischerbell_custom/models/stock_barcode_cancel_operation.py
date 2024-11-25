# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _


class StockBarcodeCancelPicking(models.TransientModel):
    _inherit = 'stock_barcode.cancel.operation'

    reason_id = fields.Many2one('stock.barcode.cancel.reason', string="Cancelation Reason")
    reason = fields.Text('Enter your reason')
    enable_reason = fields.Boolean(default=False)

    @api.onchange('reason_id')
    def _onchange_reason_id(self):
        if self.reason_id.name == "Other":
            self.enable_reason = True
        else:
            self.enable_reason = False


    def action_cancel_operation(self):
        res = self.picking_id.action_cancel()
        if self.reason_id.name == "Other":
            self.picking_id.message_post(body=self.reason, subject="DO Cancelled")    
        else:
            self.picking_id.message_post(body=self.reason_id.name, subject="DO Cancelled")
        return {'type': 'ir.actions.act_window_close', 'infos': {'cancelled': res}}


class StockBarcodeCancelReasons(models.Model):
    _name = "stock.barcode.cancel.reason"
    _description = "StockBarcodeCancelReason"

    name = fields.Char(string="Cancel Reason")
