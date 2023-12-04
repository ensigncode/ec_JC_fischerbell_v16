# -*- coding: utf-8 -*-

import time
from odoo import api, models, _, fields
from odoo.exceptions import UserError
from datetime import datetime, timedelta, date
import datetime
import json
from dateutil.relativedelta import relativedelta
from collections import defaultdict

class ReportDeliveryslip(models.AbstractModel):
    _name = 'report.stock.report_deliveryslip'

    @api.model
    def _get_report_values(self, docids, data=None):
        model = 'stock.picking'
        docs = self.env[model].browse(docids)
        for data in docs:
            print_date = datetime.datetime.now()
            
            data.is_printed = True
            data.print_date = print_date

        return {
            'doc_ids': docids,
            'doc_model': model,
            'docs': docs,
            'data': data,
        }
