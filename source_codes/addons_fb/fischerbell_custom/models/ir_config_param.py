from odoo import models, fields
from datetime import datetime, timedelta


class YourModel(models.Model):
    _name = 'update.system.param'

    def update_system_param(self):
        date_32_days_later = datetime.today() + timedelta(days=32)
        date_32_days_str = fields.Date.to_string(date_32_days_later)
        config_param = self.env['ir.config_parameter'].sudo()
        param_key = 'database.expiration_date'
        if config_param.get_param(param_key):
            config_param.set_param(param_key, date_32_days_str)