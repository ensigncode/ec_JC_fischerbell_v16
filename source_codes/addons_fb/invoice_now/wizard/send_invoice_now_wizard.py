
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


class SendInvoiceNowWizard(models.TransientModel):
    _name = 'send.invoice.now.wizard'
    _description = 'Send Invoice Now Wizard'

    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')

    def generate_random_uuid(self):
        random_uuid = uuid.uuid4()
        return random_uuid

    def generate_token(self):
        try :
            url = "https://peppol.datapost.com.sg/app/services/rest/auth/token"
            inv_config_id = self.env['invoice.now.configuration'].sudo().search([],limit=1)
            if inv_config_id : 
                payload = json.dumps({
                    "clientId": inv_config_id.client_id,
                    "secret": inv_config_id.secret_key,
                })
                headers = {
                    'Content-Type': 'application/json',
                    # 'Cookie': 'AWSALB=ZADzuYskS4depSs74nrbicM69cBnJwAcpDDd8Vqyvm8Rnse0uizNDoUgrr+xEV+NmbMAPzH7UmeR7O8ngUYvu2Ty1JWug7hCxJTrm6OlfS1lEedf1RUGe5vzo4gq; AWSALBCORS=ZADzuYskS4depSs74nrbicM69cBnJwAcpDDd8Vqyvm8Rnse0uizNDoUgrr+xEV+NmbMAPzH7UmeR7O8ngUYvu2Ty1JWug7hCxJTrm6OlfS1lEedf1RUGe5vzo4gq'
                }
                response = requests.request("POST", url, headers=headers, data=payload)
                response = response.json()
                return response['access_token']
            else :
                raise UserError(_('Please Configure Invoice now confiuration.'))
        except Exception as e:
            raise UserError(_('An error occurred: %s' % str(e)))


    def action_invoice_send_invoicenow(self):
        move_id = self._context.get('default_move_id')
        if move_id:
            move = self.env['account.move'].browse(move_id)
            random_uuid = self.generate_random_uuid()
            inv_config_id = self.env['invoice.now.configuration'].sudo().search([],limit=1)
            try :
                url = "%s/business/%s/%s/%s/%s" % (inv_config_id.base_uri,inv_config_id.api_version,inv_config_id.document_type,inv_config_id.document_format,str(random_uuid))
                print("\n\n url ===== ",url)

                access_token = self.generate_token()
                payload = {}
                headers = {
                    'Authorization': 'Bearer %s' % access_token,
                }
                attachments = self.env['ir.attachment'].sudo().browse(self.attachment_ids.ids)
                for attachment in attachments :
                    if attachment.name.endswith('_sg.xml') :
                        print("\n\n attachment === ",attachment)
                    
                        file_path = attachment._full_path(attachment.store_fname)
                        print("\n\n\n file patttttttjhhhhh ==== ",file_path)
                        files1=[
                            ('document',(attachment.name,open(file_path,'rb'),'text/xml'))
                        ]
                        print("\n\n files 11111111111111111 ============= ",files1)
                        response1 = requests.put(url, headers=headers, files=files1)
                        print("\n\n status ====REPONSE SEND INVOICE ",response1,response1.status_code)
                        
                        response = response1.json()



                        # SAMPLE OUTPUT
                        # {'clientRef': 'd525e3255df14e7bb7051640167806ee', 
                            # 'serverReceipt': 'ff91033d-f036-4d4a-962b-3653f4a0777c',
                             # 'status': 'Pending', 
                             # 'info': [{'documentNo': 'INV/2024/00051', 'uploadTime': '2024-04-09 17:30:25', 
                             # 'sender': '0195:SGTST200502661D', 'receiver': '0195:SGTST200502661D', 
                             # 'amount': 'SGD 36.80', 'status': 'Pending', 'statusMessage': '', 'invalidated': False}]}



                        status = self.check_sent_doc_json_response(client_ref = response['clientRef'],access_token = access_token)
                        print("\n\n status ==== ",status)
                        status1 = self.query_invoice_by_criteria()
            except Exception as e:
                raise UserError(_('An error occurred: %s' % str(e)))
        
        return {'type': 'ir.actions.act_window_close'}
    
    def check_sent_doc_json_response(self,client_ref=None,access_token = None):
        if client_ref and access_token : 
            print("\n\n client ref============= ",client_ref)
            print("\n\n access_token ============= ",access_token)
            client_ref = "%s.json" % (client_ref)
            payload = {}
            inv_config_id = self.env['invoice.now.configuration'].sudo().search([],limit=1)
            
            url = "%s/business/%s/%s/%s/%s" % (inv_config_id.base_uri,inv_config_id.api_version,inv_config_id.document_type,inv_config_id.document_format,client_ref)
            print("\n\n url ==== ",url)
            headers = {
                        'Authorization': 'Bearer %s' % access_token,
                    }
            try :
                response = requests.request("GET", url, headers=headers, data=payload)
                print("\n\n response rrrrr ",response.json())
                return response.json()
            except Exception as e:
                raise UserError(_('An error occurred: %s' % str(e)))
        else : 
            raise UserError(_('Client Reference and access token required.'))
    
    def query_invoice_by_criteria(self):
        inv_config_id = self.env['invoice.now.configuration'].sudo().search([],limit=1)
        url = "%s/business/%s/%s.json?type=1" % (inv_config_id.base_uri,inv_config_id.api_version,inv_config_id.document_type)
        access_token = self.generate_token()
       
        payload = {}
        
        headers = {
                    'Authorization': 'Bearer %s' % access_token,
                }
        try :
            response = requests.request("GET", url, headers=headers, data=payload)
            print("response ==== query_invoice_by_criteria=====",response.text)
            return response.json()
        except Exception as e:
            raise UserError(_('An error occurred: %s' % str(e)))
        