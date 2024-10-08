# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, _


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    expiration_date = fields.Datetime(string='Expiration Date')
    new_expiration_date = fields.Datetime(string='Expiration Date',compute='compute_expiration_date')

    def compute_expiration_date(self):
        for record in self:
            # Set new expiration date from the related lot's expiration date
            record.new_expiration_date = record.lot_id.expiration_date

            # Update the expiration_date field with the new_expiration_date value
            record.expiration_date = record.new_expiration_date
