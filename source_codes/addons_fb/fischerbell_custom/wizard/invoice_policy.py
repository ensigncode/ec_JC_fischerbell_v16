# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class InvoicePolicyWizard(models.TransientModel):
    _name = 'invoice.policy.wizard'


    purchase_method = fields.Selection([
        ('purchase', 'On ordered quantities'),
        ('receive', 'On received quantities'),
    ], string="Control Policy", help="On ordered quantities: Control bills based on ordered quantities.\n"
        "On received quantities: Control bills based on received quantities.", required=True)


    def btn_confirm(self):
        product_list = []
        purchase_id = self.env["purchase.order"].search([("id", '=', self._context.get("active_id"))])
        purchase_id.button_confirm()
        for order in purchase_id:
            if order.state == 'purchase':
                order.write({'name': self.env['ir.sequence'].next_by_code('purchase.order.po')})
                if order.picking_ids:
                    for pick in order.picking_ids:
                        pick.user = self.env.user.id
        product_list = purchase_id.order_line.mapped('product_id')
        for rec in product_list:
            rec.purchase_method = self.purchase_method
        return True