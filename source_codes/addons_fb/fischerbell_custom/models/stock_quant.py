# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    manufacturing_date = fields.Date(related='lot_id.manufacturing_date', store=True, readonly=False)

    @api.model
    def _get_inventory_fields_create(self):
        """ Returns a list of fields user can edit when he want to create a quant in `inventory_mode`.
        """
        res = super()._get_inventory_fields_create()
        res += ['manufacturing_date']
        return res

    @api.model
    def _get_inventory_fields_write(self):
        """ Returns a list of fields user can edit when he want to edit a quant in `inventory_mode`.
        """
        res = super()._get_inventory_fields_write()
        res += ['manufacturing_date']
        return res

    @api.model
    def _get_removal_strategy_order(self, removal_strategy):
        if removal_strategy == 'fmfo':
            return 'manufacturing_date ASC, id'
        return super(StockQuant, self)._get_removal_strategy_order(removal_strategy)
