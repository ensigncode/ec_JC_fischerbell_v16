# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http, _
from odoo.http import request
import base64
import json
from odoo.addons.stock_barcode.controllers.stock_barcode import StockBarcodeController

class MultiFileUploadController(http.Controller):

    @http.route('/files_upload', type='http', auth='user', methods=['POST'], csrf=False)
    def files_upload(self, **kwargs):
        record_id = int(kwargs.get('record_id'))
        record_model = kwargs.get('record_model')
        attachment_files = request.httprequest.files.getlist('attachment_files')
        res_obj = request.env[record_model].browse(record_id)
        attachment_model = request.env['ir.attachment']
        for file_data in attachment_files:
            filename = file_data.filename
            file_content = file_data.read()
            attachment = attachment_model.create({
                'name': filename,
                'datas': base64.b64encode(file_content),
                'res_model': record_model,
                'res_id': record_id,
            })
            res_obj.write({
                'upload_images': [(4, attachment.id)]
                })