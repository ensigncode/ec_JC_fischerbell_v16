
from odoo import api, fields, models, _
import requests
import json
import uuid
import logging

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    def action_invoice_now_sent(self):
        """ Open a window to compose an email, with the edi invoice template
            message loaded by default
        """
        if not self.attachment_ids:
            raise UserError(_("No attachments available for this invoice."))
        action = self.env.ref('invoice_now.send_invoice_now_wizard_action').read()[0]
        attachment_ids = []
        for attachment in self.attachment_ids:
            attachment_name = attachment.name
            if '_sg.xml' in attachment_name:
                attachment_ids.append(attachment.id)
                
        action['context'] = {
            'default_attachment_ids': [(6, 0, attachment_ids)],
            'default_move_id': self.id,
        }
        return action

    client_ref = fields.Char(string="Client Ref",tracking=True,copy=False)
    send_invoice_req_status = fields.Char(string="Send Invoice Status Code",tracking=True,copy=False)
    send_invoice_content = fields.Text(string="Send Invoice Content",copy=False)
    send_invoice_status = fields.Boolean(string="Send Invoice Status",copy=False)

    invoice_status_content = fields.Text(string="Invoice Status",copy=False)
    invoice_status = fields.Text(string="Invoice Status",copy=False)
    is_completed = fields.Boolean(string="Is Completed",copy=False)
    applicable_invoicenow = fields.Boolean(string="Applicable for Invoicenow?",related="partner_id.applicable_invoicenow")

    @api.model
    def check_invoice_status(self):
        config_id =  self.env['invoice.now.configuration'].search([],limit=1) 
        if config_id:
            config_id.action_generate_token()
            domain = [('is_completed','=',False),('move_type','in',('out_invoice','out_refund')),('state','not in',('draft','cancel'))]
            invoice_ids = self.env['account.move'].search(domain)
            for invoice in invoice_ids:
                if invoice.client_ref:
                    client_ref = invoice.client_ref
                    _logger.info('\n\n=========CLIENT REF=============%s' % client_ref)
                    url = 'https://peppol.datapost.com.sg/services/rest/peppol/business/v10/invoices/peppol-invoice-2/%s.json' %client_ref
                    payload={}
                    files={}
                    headers = {
                      'Content-Type': 'application/x-www-form-urlencoded',
                      'Authorization': 'Bearer %s' % config_id.access_token,
                    }
                    response = requests.request("GET", url, headers=headers, data=payload, files=files)
                    _logger.info('\n\n=========REFRESH============ response =====================%s' % response.status_code)
                    invoice.invoice_status_content = response.text
                    invoice.invoice_status = response.status_code
                    if response.status_code == 200:
                        response = response.json()
                        if response and 'status' in response and response['status']:
                            status = response['status']
                            if status == 'Completed':
                                invoice.is_completed = True
                        _logger.info('\n\n=========REFRESH============ response =====================%s' % response)
                    else:
                        _logger.info('\n Error while Query Documents by Client Batch Reference ::', {response.status_code}, {response.text})
        return True
