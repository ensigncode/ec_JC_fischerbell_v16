# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_round
import base64
class ReportStatementOfAccount(models.TransientModel):
    _name = 'report.statement.of.account'

    name = fields.Char('Name')
    partner_ids = fields.Many2many('res.partner', string = 'Partner')
    till_date = fields.Date(string = 'Till Date', default=fields.date.today())
    # partner_id = fields.Many2one('res.partner', 'Partner')
    # start_date = fields.Date('Start Date')
    # end_date = fields.Date('End Date')

    def print_statement_of_account(self):
        partner_list = []
        if not self.partner_ids:
            ValidationError(
                _('Partner must be selected!'))
        data = {'data':self.read()[0]}
        return self.env.ref('fischerbell_custom.action_report_statement_of_account').report_action(None, data=data)

