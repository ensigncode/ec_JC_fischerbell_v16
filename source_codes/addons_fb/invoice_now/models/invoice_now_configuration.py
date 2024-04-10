# -*- coding: utf-8 -*-
from odoo import models, fields, api
import requests
import json
import logging

_logger = logging.getLogger(__name__)


class InvoiceNowConfiguration(models.Model):
    _name = "invoice.now.configuration"
    _description = "Invoice now configuration"

    name = fields.Char(string="Name",default="Invoice Now Config")
    client_id = fields.Char(string="Client ID",default="6e000f51d2f94d2889043396a65359bc")
    secret_key = fields.Char(string="Secret Key",default="1876d8c0cc474ec48690b6810c243003")
    base_uri = fields.Char(string="Base URI",default="https://peppol.datapost.com.sg/services/rest/peppol")
    inv_document_type = fields.Char(string="Invoice Document Type",default='invoices')
    inv_document_format= fields.Char(string="Invoice Document Format",default='peppol-invoice-2')
    credit_document_type = fields.Char(string="Credit Note Document Type",default='credit-notes')
    credit_document_format = fields.Char(string="Credit Note Document Format",default='peppol-credit-note-2')
    api_version = fields.Char(string="API Version",default='v10')
    access_token = fields.Text(string="Access Token")
    refresh_token = fields.Text(string="Refresh Token")

    document_type = fields.Selection([('invoices','Invoices'),('credit_note','Credit Note'),('order','Order'),('order_response','Order Response')],string="Document Type")
    document_format = fields.Char(string="Document Format")

    def action_generate_token(self):
        try :
            url = "https://peppol.datapost.com.sg/app/services/rest/auth/token"
            payload = json.dumps({
              "clientId": self.client_id,
              "secret": self.secret_key,
            })
            headers = {'Content-Type': 'application/json'}
            response = requests.request("POST", url, headers=headers, data=payload)
            _logger.info('\n\n=========REFRESH============ response =====================%s' % response.status_code)
            
            if response.status_code == 200:
                response = response.json()
                if 'access_token' in response and response['access_token']:
                    self.access_token = response['access_token']
                    _logger.info('\n===================== Access Token =====================%s' %response['access_token'])

                if 'access_token' in response and response['access_token']:
                    self.refresh_token = response['refresh_token']
                    _logger.info('\n===================== Refresh Token =====================%s'  %response['refresh_token'])
            else:
                self.refresh_token = ''
                self.access_token = ''
                _logger.info('\n Error while generating token ::', {response.status_code}, {response.text})
        except Exception as e:
            raise UserError(_('An error occurred: %s' % str(e)))

    def action_refresh_token(self):
        if self.refresh_token:
            url = "https://peppol.datapost.com.sg/app/services/rest/auth/refreshToken"
            payload = json.dumps({
                'refresh_token':self.refresh_token,
            })
            headers = {
              'Content-Type': 'application/json',
              'Accept': 'application/json',
            }
            response = requests.request("POST", url, headers=headers, data=payload)
            if response.status_code == 200:
                response = response.json()
                if 'access_token' in response and response['access_token']:
                    self.access_token = response['access_token']
                if 'access_token' in response and response['access_token']:
                    self.refresh_token = response['refresh_token']
                _logger.info('\n=========REFRESH============ Access Token =====================%s' % response['access_token'])
                _logger.info('\n==========REFRESH=========== Refresh Token =====================%s' % response['refresh_token'])
        else:
            self.refresh_token = ''
            self.access_token = ''
            _logger.info('\n Error while generating token ::', {response.status_code}, {response.text})
        return True

    # Query Documents by Client Batch Reference
    def get_document_json_format(self):
        self.action_generate_token()

        client_refs = ['d525e3255df14e7bb7051640167806ee']
        for client_ref in client_refs:
            url = 'https://peppol.datapost.com.sg/services/rest/peppol/business/v10/invoices/peppol-invoice-2/%s.json' %client_ref
            payload={}
            files={}
            headers = {
              'Content-Type': 'application/x-www-form-urlencoded',
              'Authorization': 'Bearer %s' % self.access_token,
              # 'Cookie': 'AWSALB=IW0PMvz6KQ/cE8UL911fxSnwjYYFkG4gAJvwYNtcCmVFGq2+0bNyjkkk0YTe4LWjZiOmeNDNjOdO4wVRDeoCqfiG7Co3NQFJtI/0+RQFrlKGAR/1FPsEm9VpItEJ; AWSALBCORS=IW0PMvz6KQ/cE8UL911fxSnwjYYFkG4gAJvwYNtcCmVFGq2+0bNyjkkk0YTe4LWjZiOmeNDNjOdO4wVRDeoCqfiG7Co3NQFJtI/0+RQFrlKGAR/1FPsEm9VpItEJ'
            }

            response = requests.request("GET", url, headers=headers, data=payload, files=files)
            if response.status_code == 200:
                response = response.json()
                _logger.info('\n\n=========REFRESH============ response =====================%s' % response)

            else:
                _logger.info('\n Error while Query Documents by Client Batch Reference ::', {response.status_code}, {response.text})


        return True

    # Query Documents by Client Batch Reference
    def get_document_csv_format(self):
        self.action_generate_token()
        client_refs = ['d525e3255df14e7bb7051640167806ee']
        for client_ref in client_refs:
            url = 'https://peppol.datapost.com.sg/services/rest/peppol/business/v10/invoices/peppol-invoice-2/%s.csv' %client_ref
            payload={}
            files={}
            headers = {
              'Content-Type': 'application/x-www-form-urlencoded',
              'Authorization': 'Bearer %s' % self.access_token,
            }
            response = requests.request("GET", url, headers=headers, data=payload, files=files)
            if response.status_code == 200:
                response = response.text
                _logger.info('\n\n=========REFRESH============ response =====================%s' % response)

            else:
                _logger.info('\n Error while Query Documents by Client Batch Reference ::', {response.status_code}, {response.text})
        return True


    # Query Documents by Criteria – JSON Response
    def get_document_criteria_json_format(self):
        self.action_generate_token()
        client_refs = ['d525e3255df14e7bb7051640167806ee']
        start_documentNo = 0
        end_documentNo = 45
        type = 'SENT'
        timeFrom = ''
        timeTo = ''
        sender = ''
        receiver = ''
        status =  ''
        pageNum = ''
        pageSize = ''
        nonPeppol = ''
        downLine = ''
        for client_ref in client_refs:
            payload={}
            files={}
            headers = {
              'Content-Type': 'application/x-www-form-urlencoded',
              'Authorization': 'Bearer %s' % self.access_token,
            }
            url = 'https://peppol.datapost.com.sg/services/rest/peppol/business/v10/invoices/peppol-invoice-2/%s.json?documentNo=%s&documentNo=%s&type=%s&timeFrom=%s&timeTo=%s&sender=%s&receiver=%s&status=%s&pageNum=%s&pageSize=%s&nonPeppol=%s&downLine=%s' % (client_ref,start_documentNo,end_documentNo,type,timeFrom,timeTo,sender,receiver,status,pageNum,pageSize,nonPeppol,downLine)
            response = requests.request("GET", url, headers=headers, data=payload, files=files)
            if response.status_code == 200:
                response = response.text
                _logger.info('\n\n=========REFRESH============ response =====================%s' % response)
            else:
                _logger.info('\n Error while Query Documents by Client Batch Reference ::', {response.status_code}, {response.text})
        return True

    # Query Documents by Criteria – CSV Response
    def get_document_criteria_csv_format(self):
        self.action_generate_token()
        client_refs = ['d525e3255df14e7bb7051640167806ee']
        start_documentNo = 0
        end_documentNo = 45
        type = 'SENT'
        timeFrom = ''
        timeTo = ''
        sender = ''
        receiver = ''
        status =  ''
        pageNum = ''
        pageSize = ''
        nonPeppol = ''
        downLine = ''
        for client_ref in client_refs:
            payload={}
            files={}
            headers = {
              'Content-Type': 'application/x-www-form-urlencoded',
              'Authorization': 'Bearer %s' % self.access_token,
            }
            url = 'https://peppol.datapost.com.sg/services/rest/peppol/business/v10/invoices/peppol-invoice-2/%s.csv?documentNo=%s&documentNo=%s&type=%s&timeFrom=%s&timeTo=%s&sender=%s&receiver=%s&status=%s&pageNum=%s&pageSize=%s&nonPeppol=%s&downLine=%s' % (client_ref,start_documentNo,end_documentNo,type,timeFrom,timeTo,sender,receiver,status,pageNum,pageSize,nonPeppol,downLine)
            response = requests.request("GET", url, headers=headers, data=payload, files=files)
            if response.status_code == 200:
                response = response.text
                _logger.info('\n\n=========REFRESH============ response =====================%s' % response)
            else:
                _logger.info('\n Error while Query Documents by Client Batch Reference ::', {response.status_code}, {response.text})
        return True


    # Download Document Contents - XML
    def action_download_doc_xml(self):
        self.action_generate_token()
        client_refs = ['d525e3255df14e7bb7051640167806ee']
        documentNo = 'INV/2024/00051'
        document_type = 'invoices'
        sender = 'SGTST200502661D'
        receiver = 'SGTST200502661D'
        nonPeppol = 'Exclude'
        downLine = 'Exclude'

        payload={}
        files={}
        headers = {
          'Content-Type': 'application/x-www-form-urlencoded',
          'Authorization': 'Bearer %s' % self.access_token,
        }

        url = 'https://peppol.datapost.com.sg/apps/services/rest/peppol/business/v10/invoices/INV/2024/00051.xml'
        response = requests.request("GET", url, headers=headers, data=payload, files=files)
        _logger.info('\n\n======== response.status_code =====================%s' % response.status_code)

        return True

