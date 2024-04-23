# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models,api,fields, _

class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    picking_ticket_ids = fields.One2many('stock.picking', 'ticket_id', string='Transfers')
    delivery_count = fields.Integer(string='Delivery Orders', compute='_compute_picking_ticket_ids')

    @api.depends('picking_ticket_ids')
    def _compute_picking_ticket_ids(self):
        for order in self:
            order.delivery_count = len(order.picking_ticket_ids)

    def action_view_transfers(self):
        """Open a new window to view transfers."""
        action = self.env["ir.actions.actions"]._for_xml_id("stock.action_picking_tree_all")
        pickings = self.picking_ticket_ids
        if len(pickings) > 1:
            action['domain'] = [('id', 'in', pickings.ids)]
        elif pickings:
            form_view = [(self.env.ref('stock.view_picking_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = pickings.id
        return action


    def action_select_loc(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Create a Field Service task'),
            'res_model': 'fcb.location',
            'view_mode': 'form',
            'target': 'new',
        }


class StockPicking(models.Model):
    _inherit = 'stock.picking'
    ticket_id = fields.Many2one('helpdesk.ticket', string="Ticket Order", store=True, readonly=False, )
