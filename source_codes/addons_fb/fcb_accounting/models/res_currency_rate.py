from odoo import models, fields, api
import calendar
from datetime import date,datetime

class ResCurrencyRate(models.Model):
	_inherit = 'res.currency.rate'

	@api.model
	def _send_exchange_rate_alert(self):
		# Get the accountant user or group
		accountants_group = self.env.ref('account.group_account_manager')
		user_id = self.env.user
		accountants = accountants_group.users
		today_date = datetime.today()
		year_month = today_date.strftime('%Y-%m')
		last_day_of_month = calendar.monthrange(today_date.year, today_date.month)[1]
		currency_rates = self.env['res.currency.rate'].search([
				('name', '>=', f'{year_month}-01'),
				('name', '<=', f'{year_month}-{last_day_of_month}'),
			])
		if not currency_rates:
			# Send alert/notification to the accountants
			for accountant in accountants:
				template = self.env.ref('fcb_accounting.email_template_exchange_rate_alert')
				template.send_mail(accountant.id, force_send=True)
