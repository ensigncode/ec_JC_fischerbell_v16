# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models

class PickingAssignResponsible(models.TransientModel):
    _name = 'picking.assign.responsible'
    _description = 'Picking Assign Responsible'

    picking_ids = fields.Many2many('stock.picking' ,string='Picking ids')
    user_id = fields.Many2one('res.users', string='Responsible',
            domain=lambda self: [('groups_id', 'in', self.env.ref('stock.group_stock_user').id)],
            default=lambda self: self.env.user, required=True
        )

    def action_assign(self):
        for record in self:
            record.picking_ids.write({'user_id': record.user_id.id})