from odoo import _, api, fields, models


class PurchaseOrderRef(models.TransientModel):
    _name = 'purchase.order.ref'

    name = fields.Char('Name')

    def action_confirm_purchase_ref(self):
        return {'type': 'ir.actions.act_window_close'}
