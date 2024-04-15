from odoo import models,fields, api, _
from odoo.exceptions import UserError, ValidationError
import requests
import json
import base64
import http.client
import mimetypes
from codecs import encode
import uuid
import random
import string
import logging

_logger = logging.getLogger(__name__)


class SendInvoice(models.TransientModel):
	_name = 'send.invoice.lines'
	_description = 'Send Invoice'

	attachment_id = fields.Many2one('ir.attachment',string="Attachment")
	move_id = fields.Many2one('account.move')
	send_invoice_id = fields.Many2one('send.invoice')

class SendInvoice(models.TransientModel):
	_name = 'send.invoice'
	_description = 'Send Invoice Lines'

	move_type = fields.Selection([('out_invoice','Invoice'),('out_refund','Credit Note')],string="Move Type")
	send_invoice_ids = fields.One2many('send.invoice.lines','send_invoice_id',string="Send Invoice")

	@api.model
	def default_get(self,vals):
		res = super(SendInvoice,self).default_get(vals)
		ctx = self.env.context
		if 'default_move_type' in ctx and ctx['default_move_type'] and ctx['default_move_type'] in ('out_invoice','out_refund'):
			res['move_type'] =  ctx['default_move_type']
		else:
			raise UserError(_('Send Invoice to peppol datapost is allowed to customer invoice and credeit note.'))
		invoice_lines = []
		active_ids = self.env.context.get('active_ids',False)
		move_ids = self.env['account.move'].browse(active_ids)
		for move in move_ids:
			attachment_ids = move.attachment_ids
			if attachment_ids and attachment_ids.filtered(lambda x:'_sg.xml' in x.name):
				attachment_id = attachment_ids.filtered(lambda x:'_sg.xml' in x.name)
				invoice_lines.append((0,0,{'move_id':move.id,'attachment_id':attachment_id.id}))
		res['send_invoice_ids'] = invoice_lines
		return res

	def send_invoice_datapost(self,invoice_id,attachment_id,config_id,document_type,document_format):
		if config_id and invoice_id.partner_id.applicable_invoicenow and not invoice_id.send_invoice_status:
			config_id.action_generate_token()
			if config_id.access_token:
				headers = {'Authorization': 'Bearer %s' % config_id.access_token}
				client_ref = uuid.uuid4()
				config_id.action_generate_token()
				# CORRECT INVOICE URL :: https://peppol.datapost.com.sg/services/rest/peppol/business/v10/invoices/peppol-invoice-2/5fd96e60-1f95-4659-922a-9f7d2c8bf6b5
				url = "%s/business/%s/%s/%s/%s" % (config_id.base_uri,config_id.api_version,document_type,document_format,str(client_ref))
				_logger.info('\n ========url=======%s' %url)
				payload = {}
				headers = {
					'Authorization': 'Bearer %s' % config_id.access_token,
				}
				file_path = attachment_id._full_path(attachment_id.store_fname)
				files = [('document',(attachment_id.name,open(file_path,'rb'),'text/xml'))]
				response = requests.put(url, headers=headers, files=files)
				_logger.info('\n ========STATUS CODE & TEXT=======%s--------------\n\n\n%s\n\n\n' %(response.status_code,response.text))
				invoice_id.send_invoice_req_status = response.status_code
				invoice_id.send_invoice_content = response.text
				if response.status_code in (200,202):
					response = response.json()
					invoice_id.send_invoice_content = response
					invoice_id.send_invoice_status = True
					invoice_id.client_ref = client_ref
				else:
					_logger.info('\n ========STATUS CODE & TEXT=======%s-%s' %(response.status_code,response.text))
		return True

	def action_send_invoice(self):
		config_id =  self.env['invoice.now.configuration'].search([],limit=1) 
		if not config_id:
			raise UserError(_('Please configure for the Invoice Now Configuration for Document Type Invoice.'))
		
		if self.move_type == 'out_invoice':
			document_type = config_id.inv_document_type
			document_format = config_id.inv_document_format
		else:
			document_type = config_id.credit_document_type
			document_format = config_id.credit_document_format

		for line in self.send_invoice_ids:
			self.send_invoice_datapost(line.move_id,line.attachment_id,config_id,document_type,document_format)
		return True
