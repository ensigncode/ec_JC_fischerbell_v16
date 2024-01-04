
from odoo import api,fields, models, _
from datetime import datetime, timedelta, date
import pytz


class CrmLead(models.Model):
    _inherit = 'crm.lead'


    def cron_remainder_to_salesperson(self):
        user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
        today = user_tz.localize(fields.Datetime.from_string(fields.Date.context_today(self))) - timedelta(days=1)
        date_start = today.astimezone(pytz.timezone('UTC'))
        date_stop = date_start + timedelta(days=1, seconds=-1)
        for rec in self.search([('create_date', '>=', date_start),
                                ('create_date', '<=', date_stop)]):
            quotation_count = len(rec.order_ids.filtered_domain(self._get_lead_quotation_domain()))
            if quotation_count == 0:
                display_message = """
                						<p><b>Quotation Is Not Done</b></p>
                						<p>Leads : """ + rec.name + """
                						"""
                subject = (f""" Quotation Is Not Done %s""" % rec.name)
                email_to = rec.user_id.email_formatted
                mails = {
                    'subject': subject,
                    'email_from': self.env.user.email_formatted,
                    'email_to': email_to,
                    'body_html': display_message,
                    'auto_delete': False,
                }
                mail = self.env['mail.mail'].create(mails)
                mail.send()




