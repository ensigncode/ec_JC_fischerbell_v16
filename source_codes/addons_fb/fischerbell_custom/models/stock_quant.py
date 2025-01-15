# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    expiration_date = fields.Datetime(string='Expiration Date')
    new_expiration_date = fields.Datetime(string='Expiration Date',compute='compute_expiration_date')
    po_source_type = fields.Selection(
        [('po', 'From Purchase Order'),
         ('service', 'From Service'),
         ('other', 'Other')],
        string='Source Type',
        compute='_compute_source_type',
        store=True
    )

    @api.depends('lot_id', 'lot_id.is_from_po', 'lot_id.is_from_service')
    def _compute_source_type(self):
        for record in self:
            if record.lot_id.is_from_po:
                record.po_source_type = 'po'
            elif record.lot_id.is_from_service:
                record.po_source_type = 'service'
            else:
                record.po_source_type = 'other'

    def compute_expiration_date(self):
        for record in self:
            # Set new expiration date from the related lot's expiration date
            record.new_expiration_date = record.lot_id.expiration_date

            # Update the expiration_date field with the new_expiration_date value
            record.expiration_date = record.new_expiration_date


    @api.model
    def action_view_inventory(self):
        result = super(StockQuant, self).action_view_inventory()
        if result.get('context'):
            result['context'].update({'search_default_po_source_type_group': 1})
        return result
 