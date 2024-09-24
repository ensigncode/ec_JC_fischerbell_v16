# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class InvoicePolicyWizard(models.TransientModel):
    _name = 'invoice.policy.wizard'


    purchase_method = fields.Selection([
        ('purchase', 'On Ordered quantities'),
        ('receive', 'On Received quantities'),
    ], string="Control Policy", help="On ordered quantities: Control bills based on ordered quantities.\n"
        "On received quantities: Control bills based on received quantities.", required=False)

    invoice_policy = fields.Selection(
        [('order', 'Ordered quantities'),
         ('delivery', 'Delivered quantities')], string='Invoicing Policy',
        help='Ordered Quantity: Invoice quantities ordered by the customer.\n'
             'Delivered Quantity: Invoice quantities delivered to the customer.')

    def btn_confirm(self):
        product_list = []
        if self._context.get("active_model") == 'purchase.order' and self._context.get("is_purchase"):
            purchase_id = self.env["purchase.order"].search([("id", '=', self._context.get("active_id"))])
            line_ids = purchase_id.order_line.filtered(lambda x:x.product_id.detailed_type != 'service').mapped('product_id').write({'purchase_method':self.purchase_method})
            purchase_id.button_confirm()
        if self._context.get("active_model") == 'sale.order' and self._context.get("is_sale"):
            sale_id = self.env["sale.order"].search([("id", '=', self._context.get("active_id"))])
            line_ids = sale_id.order_line.filtered(lambda x:x.product_id.detailed_type != 'service').mapped('product_id').write({'invoice_policy':self.invoice_policy})
            sale_id.action_confirm()

        return True