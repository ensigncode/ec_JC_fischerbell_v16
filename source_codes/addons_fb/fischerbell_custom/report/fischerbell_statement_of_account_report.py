from odoo import models, api, fields
import base64
import logging
import pdb

_logger = logging.getLogger(__name__)


class SOAReport(models.AbstractModel):
    _name = 'report.fischerbell_custom.fischerbell_report_soa_document'
    _description = 'SOA Report'


    def get_partner_data(self, data):
        partner_list = []
        if data or data is not None:
            partner_ids = self.env['res.partner'].browse(data.get('partner_ids'))
            for partner in partner_ids:
                till_date = data.get('till_date')
                list_move = []
                invoice_ids = self.env['account.move'].sudo().search([
                    ('partner_id.parent_id', '=', partner.id) or ('partner_id', '=', partner.id),
                    ('invoice_date', '<=', till_date),
                    ('move_type', '=', 'out_invoice')
                ])
                for inv in invoice_ids:
                    list_move.append(inv.id)
                payment_ids = self.env['account.move'].sudo().search([
                    ('partner_id', '=', partner.id),
                    ('date', '<=', till_date),
                    ('move_type', '=', 'entry')
                ])
                for payment in payment_ids:
                    list_move.append(payment.id)
                account_move_ids = self.env['account.move'].search([('id', 'in', list_move)])
                if not account_move_ids.ids:
                    partner_list.append({'partner_id':partner, 'account_move_ids':False, 'total_partner_currency': 0, 'total_company_currency': 0})
                    pass
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
                if account_move_ids.ids:
                    try:
                        pdf_data = self.env["ir.actions.report"].sudo().with_context(from_email=True)._render_qweb_pdf('fischerbell_custom.action_report_statement_of_account', account_move_ids.ids, data={'report_type': 'pdf'})[0]
                    except Exception as e:
                        _logger.error('Error generating PDF: %s', str(e))
                        continue
                    attachment_data = {
                        'name': 'Statement Of Account.pdf',
                        # 'datas': pdf_data[0] if pdf_data else False,
                        'datas': base64.encodebytes(pdf_data),
                    }
                    mail = self.env['mail.mail'].create({
                        'subject': 'Statement Of Account',
                        'body_html': 'Statement Of Account',
                        'email_to': partner.soa_email,
                        'partner_ids': [(4, partner.id)],
                        'attachment_ids': [(0, 0, attachment_data)],
                    })
                    mail.send()
                partner_list.append({'partner_id':partner, 'account_move_ids':account_move_ids or False})
        for rec in partner_list:
            total_partner_currency = 0
            total_company_currency = 0
            if rec.get('account_move_ids'):
                for moves in rec['account_move_ids']:
                    company_total = moves.currency_id.compute(moves.amount_total_in_currency_signed, moves.company_id.currency_id)
                    partner_total = moves.currency_id.compute(moves.amount_total_in_currency_signed, rec['partner_id'].currency_id)
                    total_partner_currency += partner_total
                    total_company_currency += company_total
                rec['total_partner_currency'] = total_partner_currency
                rec['total_company_currency'] = total_company_currency
        return partner_list

    def convert_to_partner_currency(self, amount, to_currency):
        date = fields.date.today()
        company = self.env.user.company_id
        company_currency_id = company.currency_id
        to_currency = to_currency.filtered(lambda x: x.id != company_currency_id.id)
        value = company_currency_id._convert(amount,to_currency,company,date)
        return value,to_currency.name, to_currency.id

    def convert_to_company_currency(self, amount, to_currency):
        date = fields.date.today()
        company = self.env.user.company_id
        company_currency_id = company.currency_id
        value = company_currency_id._convert(amount,to_currency,company,date)
        return value

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['account.move'].browse(docids)
        is_all_partner = True
        if self.env.context.get('from_email'):
            is_all_partner = False
        return {
            'doc_ids': docs,
            'get_data': self.get_partner_data,
            'is_all_partner':is_all_partner,
            'partner_currency':self.convert_to_partner_currency,
            'company_currency':self.convert_to_company_currency,
        }
