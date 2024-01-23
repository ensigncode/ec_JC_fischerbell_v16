# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.tools import float_compare

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def get_pricelist_price(self,product_id):
        pricelist_rule = self.pricelist_item_id
        order_date = self.order_id.date_order or fields.Date.today()
        product = product_id.with_context(**self._get_product_price_context())
        qty = 1.0
        uom = product_id.uom_id
        price = pricelist_rule._compute_price(
            product, qty, uom, order_date, currency=self.currency_id)
        return max(product_id.list_price, price)

    def sub_product_price(self,product_id):
        line = self
        price = line.get_pricelist_price(product_id)
        price_unit = product_id._get_tax_included_unit_price(
            line.company_id,
            line.order_id.currency_id,
            line.order_id.date_order,
            'sale',
            fiscal_position=line.order_id.fiscal_position_id,
            product_price_unit=price,
            product_currency=line.currency_id
        )
        return price_unit

    @api.depends('product_id', 'product_uom', 'product_uom_qty')
    def _compute_price_unit(self):
        for line in self:
            if line.qty_invoiced > 0:
                continue
            if not line.product_uom or not line.product_id or not line.order_id.pricelist_id:
                line.price_unit = 0.0
            else:
                price = line.with_company(line.company_id)._get_display_price()
                line.price_unit = line.product_id._get_tax_included_unit_price(
                    line.company_id,
                    line.order_id.currency_id,
                    line.order_id.date_order,
                    'sale',
                    fiscal_position=line.order_id.fiscal_position_id,
                    product_price_unit=price,
                    product_currency=line.currency_id
                )
            mrp_route_id = self.env.ref('mrp.route_warehouse0_manufacture')
            mto_route_id = self.env.ref('stock.route_warehouse0_mto')
            if mrp_route_id and mto_route_id and (mrp_route_id in line.product_id.route_ids) or (mto_route_id in line.product_id.route_ids) and line.product_id.bom_ids:
                boms = line.product_id.bom_ids._bom_find(line.product_id, company_id=line.company_id.id, bom_type='phantom')[line.product_id]
                if boms:
                    product_price = 0
                    for bom_line in boms[0].bom_line_ids:
                        sub_product_price = line.sub_product_price(bom_line.product_id)
                        product_price += sub_product_price
                    if  product_price > 0 and line.product_id.min_price  <= product_price and product_price <= line.product_id.max_price:
                        line.price_unit = product_price
                        