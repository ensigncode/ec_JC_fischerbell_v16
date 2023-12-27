
from odoo import api,fields, models, _
from datetime import datetime, timedelta, date


class CrmLead(models.Model):
    _inherit = 'crm.lead'


    def cron_remainder_to_salesperson(self):
        for rec in self.search([]):
            rec.quotation_count = len(rec.order_ids.filtered_domain(self._get_lead_quotation_domain()))
            if rec.quotation_count == 0:
                print("========fields.Date.today()",fields.Date.today() - timedelta(days=1))
                res = rec.search([('create_date', '=', fields.Date.today() - timedelta(days=1))])
                print('-------res',res)
            # ('create_date', '<=', fields.Date.today())
            # quotations = rec.order_ids.filtered_domain(rec._get_lead_quotation_domain())
            # print("----------->>>>>>quotations", quotations)
            # if len(quotations) < 0:
            #     # rec.search([
            #     #     #     ('stage_id', 'ilike', 'new'),
            #     #     #     ('date_order', '<=', fields.Date.today() - timedelta(days=7)),
            #     #     # ])
            #     print("----------->>>>>>quotations",quotations)


