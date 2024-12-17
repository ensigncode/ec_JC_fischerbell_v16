# -*- coding: utf-8 -*-

from odoo import models


class MailTemplate(models.Model):
    _inherit = "mail.template"

    def generate_email(self, res_ids, fields):
        res = super().generate_email(res_ids, fields)
        multi_mode = True
        if isinstance(res_ids, int):
            res_ids = [res_ids]
            multi_mode = False

        if self.model not in ['account.move', 'account.payment']:
            return res

        records = self.env[self.model].browse(res_ids)
        for record in records:
            record_data = (res[record.id] if multi_mode else res)
            record_data['attachment_ids'] = []
            if record.sale_id:
                attachments_ids = record.invoice_attchmnets.split(',')
                attachments_list = [int(attachments_id) for attachments_id in attachments_ids if attachments_id]
                if len(attachments_list) > 0:
                    record_data['attachment_ids'] = attachments_list
        return res
