# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api,fields, models, _
from odoo.tools import config, date_utils, get_lang, float_compare, float_is_zero
import markupsafe
import base64
from odoo.exceptions import RedirectWarning, UserError, ValidationError


class AccountReport(models.Model):
    _inherit = 'account.report'

    def _init_options_buttons(self, options, previous_options=None):
        options['buttons'] = [
            {'name': _('PDF'), 'sequence': 10, 'action': 'export_file', 'action_param': 'export_to_pdf', 'file_export_type': _('PDF')},
            {'name': _('XLSX'), 'sequence': 20, 'action': 'export_file', 'action_param': 'export_to_xlsx', 'file_export_type': _('XLSX')},
            {'name': _('Save'), 'sequence': 100, 'action': 'open_report_export_wizard'},
            {'name': _('Send Email'), 'sequence': 100, 'action': 'send_email_to_customer'},
        ]
    
    def send_email_to_customer(self, options):
        self.ensure_one()
        if not options.get('partner_ids'):
            raise ValueError(_("Please provide partner IDs in options."))
        
        partners = self.env['res.partner'].browse(options['partner_ids'])
        if not partners:
            raise ValueError(_("No partners found for the provided IDs."))

        # Ensure assets are committed for wkhtmltopdf
        if not config['test_enable']:
            self = self.with_context(commit_assetsbundle=True)

        base_url = self.env['ir.config_parameter'].sudo().get_param('report.url') or self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        
        for partner in partners:
            # Update options for the current partner
            partner_options = options.copy()
            partner_options['partner_ids'] = [partner.id]
            
            rcontext = {
                'mode': 'print',
                'base_url': base_url,
                'company': self.env.company,
            }

            print_mode_self = self.with_context(print_mode=True)
            print_options = print_mode_self._get_options(previous_options=partner_options)
            body_html = print_mode_self.get_html(print_options, self._filter_out_folded_children(print_mode_self._get_lines(print_options)))
            body = self.env['ir.ui.view']._render_template(
                "account_reports.print_template",
                values=dict(rcontext, body_html=body_html),
            )
            footer = self.env['ir.actions.report']._render_template("web.internal_layout", values=rcontext)
            footer = self.env['ir.actions.report']._render_template("web.minimal_layout", values=dict(rcontext, subst=True, body=markupsafe.Markup(footer.decode())))

            landscape = False
            if len(print_options['columns']) * len(print_options['column_groups']) > 5:
                landscape = True

            file_content = self.env['ir.actions.report']._run_wkhtmltopdf(
                [body],
                footer=footer.decode(),
                landscape=landscape,
                specific_paperformat_args={
                    'data-report-margin-top': 10,
                    'data-report-header-spacing': 10,
                    'data-report-margin-bottom': 15,
                }
            )
            file_name = f"{partner.name}_Account_Report.pdf"

            # Prepare and send the email
            if not partner.email:
                raise UserError(_("The partner %s (ID: %d) does not have an email address.") % (partner.name, partner.id))

            email_values = {
                'subject': _('Your Aged Receivable Report'),
                'body_html': _('Please find the attached account report specific to your account.'),
                'email_to': partner.email,
                'email_from': self.env.user.email or self.env.company.email,
                'attachment_ids': [(0, 0, {
                    'name': file_name,
                    'type': 'binary',
                    'datas': base64.b64encode(file_content).decode('utf-8'),
                    'mimetype': 'application/pdf',
                })],
            }
            mail = self.env['mail.mail'].create(email_values)
            mail.send()

        # Notify user about the successful email sending
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Emails Sent'),
                'message': _('The account reports have been sent successfully to all selected partners.'),
                'type': 'success',
                'sticky': False,
            },
        }
