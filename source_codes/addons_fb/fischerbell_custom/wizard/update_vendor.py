# -*- coding: utf-8 -*-
from odoo import fields, models, api


class WizVendors(models.TransientModel):
    _name = 'update.product.vendor'
    _description = 'Add custom vendors in product'

    @api.model
    def default_get(self, fields):
        res = super(WizVendors, self).default_get(fields)
        sale_id = self.env["sale.order"].search([("id", '=', self._context.get("active_id"))])
        line_ids = sale_id.order_line.filtered(lambda line_s: not line_s.product_template_id.seller_ids).mapped(
            lambda line: (0, 0, {'product_id': line.product_id.id,
                                 "demand_qty": line.product_uom_qty,
                                 }))
        res.update({'product_vendor_line': line_ids})
        return res

    product_vendor_line = fields.One2many("update.product.vendor.line", "product_vendor_id", string="Avaliable")

    def confirm(self):
        sale_id = self.env["sale.order"].search([("id", '=', self._context.get("active_id"))])
        for line in self.product_vendor_line:
            seller_info = (0, 0, {'partner_id': line.partner_id.id, 'min_qty': line.product_qty})
            line.product_id.update({'seller_ids': [seller_info]})
        sale_id.with_context(vendor_wizard=True).action_confirm()

class WizVendorsLine(models.TransientModel):
    _name = 'update.product.vendor.line'
    _description = 'Add custom vendors in product'

    product_vendor_id = fields.Many2one("update.product.vendor")
    partner_id = fields.Many2one('res.partner', string="Product Vendors", domain=[('supplier_rank', '>', 0)],
                                 required=True)
    product_id = fields.Many2one("product.product")
    demand_qty = fields.Float("Demand Qty")
    product_qty = fields.Float('Quantity')
