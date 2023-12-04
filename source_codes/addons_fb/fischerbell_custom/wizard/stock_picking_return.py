# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round


class ReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    is_return_loan = fields.Boolean("Is Return Loan", default=False)
    purchase_id = fields.Many2one('purchase.order', 'Purchase Order')

    @api.model
    def default_get(self, fields):
        res = super(ReturnPicking, self).default_get(fields)
        if self.env.context.get('active_id') and self.env.context.get('active_model') == 'stock.picking':
            if len(self.env.context.get('active_ids', list())) > 1:
                raise UserError(_("You may only return one picking at a time."))
            picking = self.env['stock.picking'].browse(self.env.context.get('active_id'))
            if picking.exists():
                res.update({'picking_id': picking.id})
                if picking.purchase_id:
                    res.update({'purchase_id': picking.purchase_id.id})
        return res

    def _prepare_picking_default_values(self):
        context = self._context

        vals = False
        if context.get('loan_orders') == True:
            vals = {
                'move_ids': [],
                'picking_type_id': self.picking_id.picking_type_id.return_picking_type_id.id or self.picking_id.picking_type_id.id,
                'state': 'draft',
                'origin': _("Return of %s") % self.picking_id.name,
                'is_return_loan': True
            }
        else:
            vals = {
                'move_ids': [],
                'picking_type_id': self.picking_id.picking_type_id.return_picking_type_id.id or self.picking_id.picking_type_id.id,
                'state': 'draft',
                'origin': _("Return of %s") % self.picking_id.name,
                'is_return_loan': True
            }
        # TestPickShip.test_mto_moves_return, TestPickShip.test_mto_moves_return_extra,
        # TestPickShip.test_pick_pack_ship_return, TestPickShip.test_pick_ship_return, TestPickShip.test_return_lot
        if self.purchase_id:
            ctx = dict(self.env.context)
            ctx.update({'is_purchase_return': True})
            vals['is_purchase_return'] = True

        if self.picking_id.location_dest_id:
            vals['location_id'] = self.picking_id.location_dest_id.id
        if self.location_id:
            vals['location_dest_id'] = self.location_id.id
        return vals
