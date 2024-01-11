# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.tools import float_compare

class MrpBom(models.Model):
    _inherit = "mrp.bom"

    sales_price = fields.Float(string="Sales Price")

    def calc_sales_price(self):
        return sum(line.pricelist_price for line in self.bom_line_ids)

    def write(self,vals):
        res = super(MrpBom,self).write(vals)
        if 'bom_line_ids' in vals:
            for bom in self:
                bom.sales_price = bom.calc_sales_price()
        return res

    @api.model
    def create(self,vals):
        res = super(MrpBom,self).create(vals)
        res.sales_price = res.calc_sales_price()
        return res

class MrpBomLine(models.Model):
    _inherit = "mrp.bom.line"

    pricelist_price = fields.Float(string="Pricelist Price")

    @api.onchange('product_id')
    def default_pricelist_price(self):
        for line in self:
            price = 0
            price_unit = line.product_id._get_tax_included_unit_price(line.company_id,line.company_id.currency_id,fields.Date.today(),'sale',fiscal_position=False,product_price_unit=line.product_id.list_price,product_currency=line.company_id.currency_id)
            line.pricelist_price = price_unit
