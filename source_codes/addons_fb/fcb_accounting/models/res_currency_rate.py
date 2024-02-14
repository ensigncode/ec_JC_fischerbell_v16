from odoo import models, fields, api
import calendar
import logging
from datetime import date,datetime
_logger = logging.getLogger(__name__)

class ResCurrencyRate(models.Model):
	_inherit = 'res.currency.rate'

	@api.model
	def _send_exchange_rate_alert(self):
		group_id = self.env.ref('account.group_account_manager')
		_logger.info('>>>>>>>group_idgroup_idgroup_id>>>>>>>>>>>>>>>>>>>',group_id)

		user_ids = self.env['res.users'].sudo().search([])
		_logger.info('>>>>>>>user_idsuser_idsuser_ids>>>>>>>>>>>>>>>>>>>',user_ids)

		accountants = user_ids.filtered(lambda x:group_id.id in x.groups_id.ids)
		_logger.info('>>>>>>>currency_ratescurrency_rates>>>>>>>>>>>>>>>>>>>',accountants)
		
		today_date = datetime.today()
		year_month = today_date.strftime('%Y-%m')
		last_day_of_month = calendar.monthrange(today_date.year, today_date.month)[1]
		_logger.info('>>>>>>>last_day_of_monthlast_day_of_month>>>>>>>>>>>>>>>>>>>',last_day_of_month)


		currency_rates = self.env['res.currency.rate'].search([
				('name', '>=', f'{year_month}-01'),
				('name', '<=', f'{year_month}-{last_day_of_month}'),
			])
		_logger.info('>>>>>>>currency_ratescurrency_rates>>>>>>>>>>>>>>>>>>>',currency_rates)
		if not currency_rates:
			# Send alert/notification to the accountants
			for accountant in accountants:
				_logger.info('>>>>>>>accountantaccountantaccountant>>>>>>>>>>>>>>>>>>>',accountant)

				template = self.env.ref('fcb_accounting.email_template_exchange_rate_alert')
				_logger.info('>>>>>>>template>template>>>>>>>>>>>>>>>>>>',template)

				template.send_mail(accountant.id, force_send=True)
