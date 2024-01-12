# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_round
import base64
class ReportStatementOfAccount(models.TransientModel):
    _name = 'report.statement.of.account'

    name = fields.Char('Name')
    partner_id = fields.Many2one('res.partner', 'Partner')
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')

    def print_statement_of_account(self):
        start_date = self.start_date
        end_date = self.end_date
        context = self.env.context

        if end_date < start_date:
            raise ValidationError('Please select end date greater than start date')

        list_move = []
        invoice_ids = self.env['account.move'].sudo().search([
            ('partner_id.parent_id','=',self.partner_id.id) or ('partner_id', '=', self.partner_id.id),
            ('invoice_date', '>=', start_date),
            ('invoice_date', '<=', end_date),
            ('move_type','=','out_invoice')
        ])
        for inv in invoice_ids:
            list_move.append(inv.id)

        payment_ids = self.env['account.move'].sudo().search([
            ('partner_id', '=', self.partner_id.id),
            ('date', '>=', start_date),
            ('date', '<=', end_date),
            ('move_type','=','entry')
        ])
        for payment in payment_ids:
            list_move.append(payment.id)


        account_move_ids = self.env['account.move'].search([('id','in',list_move)])

        if not account_move_ids.ids:
            raise ValidationError(
                _('There is no entries between selected '
                    'date %s and %s') % (start_date, end_date))

        positive_total_amount = 0
        negative_total_amount = 0
        for move in account_move_ids:
            if move.move_type == 'out_invoice':
                positive_total_amount += move.amount_total
            else:
                negative_total_amount += -move.amount_total

        total = positive_total_amount + negative_total_amount
        for move2 in account_move_ids:
            move2.write({'total_balance_due': total})

        # self.env.ref('fischerbell_custom.action_report_statement_of_account').report_action(account_move_ids.ids)
        if account_move_ids:
            pdf_data = self.env["ir.actions.report"].sudo()._render_qweb_pdf('fischerbell_custom.action_report_statement_of_account', account_move_ids.ids,
                                                                     data={'report_type': 'pdf'})[0]
            attachment_data = {
                'name': 'Statement Of Account.pdf',
                # 'datas': pdf_data[0] if pdf_data else False,
                'datas': base64.encodebytes(pdf_data),
            }
            mail = self.env['mail.mail'].create({
                'subject': 'Statement Of Account',
                'body_html': 'Statement Of Account',
                'email_to': self.partner_id.soa_email,
                'partner_ids': [(4, self.partner_id.id)],
                'attachment_ids': [(0, 0, attachment_data)],
            })
            mail.send()
        return self.env.ref('fischerbell_custom.action_report_statement_of_account').report_action(account_move_ids.ids)

