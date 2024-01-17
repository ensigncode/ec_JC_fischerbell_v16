# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.tools.misc import format_date

class PartnerLedgerCustomHandlerCustom(models.AbstractModel): 
    _inherit="account.partner.ledger.report.handler"

    def _get_report_line_move_line(self, options, aml_query_result, partner_line_id, init_bal_by_col_group, level_shift=0):
        res = super(PartnerLedgerCustomHandlerCustom,self)._get_report_line_move_line(options=options,aml_query_result = aml_query_result,partner_line_id = partner_line_id,init_bal_by_col_group = init_bal_by_col_group,level_shift=level_shift)
        columns = []
        report = self.env['account.report']
        for column in options['columns']:
            col_expr_label = column['expression_label']
            if col_expr_label == 'ref':
                col_value = report._format_aml_name(aml_query_result['name'], aml_query_result['ref'], aml_query_result['move_name'])
            else:
                col_value = aml_query_result[col_expr_label] if column['column_group_key'] == aml_query_result['column_group_key'] else None

            if col_value is None:
                columns.append({})
            else:
                col_class = 'number'

            if col_expr_label == 'amount_currency':
                currency = self.env['res.currency'].browse(aml_query_result['currency_id'])
                formatted_value = report.format_value(col_value, currency=currency, figure_type=column['figure_type'])
                print("\n\n formatted_value ===== ",formatted_value)

        for column in res['columns'] : 
            if 'name' in column and column['name'] == formatted_value :
                column['name'] = ""

        res['name'] = ""

        return res