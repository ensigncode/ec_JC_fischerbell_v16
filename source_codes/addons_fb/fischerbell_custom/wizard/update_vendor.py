# -*- coding: utf-8 -*-
from odoo import fields, models, api


class WizVendors(models.TransientModel):
    _name = 'update.product.vendor'
    _description = 'Add custom vendors in product'

    @api.model
    def default_get(self, fields):
        res = super(WizVendors, self).default_get(fields)
        sale_id = self.env["sale.order"].search([("id", '=', self._context.get("active_id"))])
        # line_ids = sale_id.order_line.filtered(lambda line_s: not line_s.product_template_id.seller_ids).mapped(
        #     lambda line: (0, 0, {'product_id': line.product_id.id,
        #                          "demand_qty": line.product_uom_qty,
        #                          }))

        if 'line_ids' in self._context:
            res.update({'product_vendor_line': self._context['line_ids']})
        return res

    product_vendor_line = fields.One2many("update.product.vendor.line", "product_vendor_id", string="Avaliable")

    def confirm(self):
        sale_id = self.env["sale.order"].search([("id", '=', self._context.get("active_id"))])
        for line in self.product_vendor_line:
            vals = {'partner_id': line.partner_id.id, 'min_qty': line.product_qty,'product_tmpl_id':line.product_id.product_tmpl_id.id}
            sale_line_vals = {'sale_line_id': line.sale_line_id.id, 'sale_id': line.sale_line_id.order_id.id,'product_id':line.product_id.id,'partner_id': line.partner_id.id,'bom_line_id':line.bom_line_id.id if line.bom_line_id else False}
           

            if (line.product_id.seller_ids and line.partner_id.id not in line.product_id.seller_ids.ids) or not line.product_id.seller_ids:
                seller_info = (0, 0,vals)
                line.product_id.update({'seller_ids': [seller_info]})

            supplier_info_id = line.product_id.seller_ids.filtered(lambda x:x.partner_id.id == line.partner_id.id)
            if supplier_info_id:
                sale_line_vals.update({'supplier_info_id':supplier_info_id[0].id})
            check_vendor_product_conf_line_id = sale_id.product_vendor_conf_ids.filtered(lambda x:x.sale_line_id.id == line.sale_line_id.id and x.product_id.id == line.product_id.id)
            if check_vendor_product_conf_line_id and check_vendor_product_conf_line_id[0]:
                check_vendor_product_conf_line_id = check_vendor_product_conf_line_id[0]
                check_vendor_product_conf_line_id.update(sale_line_vals)
            else:
                self.env['product.vendor.conf'].create(sale_line_vals)
        sale_id.with_context(vendor_wizard=True).approval_order()

class WizVendorsLine(models.TransientModel):
    _name = 'update.product.vendor.line'
    _description = 'Add custom vendors in product'

    product_vendor_id = fields.Many2one("update.product.vendor")
    partner_id = fields.Many2one('res.partner', string="Product Vendors", domain=[('supplier_rank', '>', 0)],
                                 required=True)
    product_id = fields.Many2one("product.product")
    demand_qty = fields.Float("Demand Qty")
    product_qty = fields.Float('Quantity')
    sale_line_id = fields.Many2one("sale.order.line")
    bom_line_id = fields.Many2one('mrp.bom.line',string="MRP BOM Line")

