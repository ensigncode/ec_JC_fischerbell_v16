# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_round

class ReportLoanItem(models.TransientModel):
    _name = 'report.loan.item'

    name = fields.Char('Name')
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')

    def print_loan_item(self):
        start_date = self.start_date
        end_date = self.end_date
        context = self.env.context

        if end_date < start_date:
            raise ValidationError('Please select end date greater than start date')

        sale_line_ids = self.env['sale.order.line'].sudo().search([
            ('order_id.date_order', '>=', start_date),
            ('order_id.date_order', '<=', end_date),
            ('order_id.type', '=', 'loan')])
        if not sale_line_ids.ids:
            raise ValidationError(
                _('There is no loan items between selected '
                    'date %s and %s') % (start_date, end_date))


        return self.env.ref('fischerbell_custom.fischerbell_loan_item_report_action').report_action(sale_line_ids.ids)