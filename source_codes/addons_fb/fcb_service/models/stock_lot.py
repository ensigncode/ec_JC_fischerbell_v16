# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from dateutil.relativedelta import relativedelta
import pytz
from collections import defaultdict
from datetime import datetime, timedelta


class StockLot(models.Model):
	_inherit = "stock.lot"

	def _send_reminder_expire_date(self):
		stock_lot_ids = self.env['stock.lot'].search([])
		utc_now = fields.Datetime.now().astimezone(pytz.utc).date()
		mail_info = {}
		expiration_date = False
		for record in stock_lot_ids:
			if record.sale_order_ids:
				sale_order_id = record.sale_order_ids[-1]
				if record.expiration_date:
					expiration_date = record.expiration_date.date()
					reminder_date = record.expiration_date.date() - relativedelta(years=1)
					if reminder_date == utc_now:
						partner_id_id = sale_order_id.partner_id.id if sale_order_id and sale_order_id.partner_id else False
						if partner_id_id:
							if partner_id_id not in mail_info:
								mail_info[partner_id_id] = {record.product_id.name: [record.name]}
							else:
								if not record.product_id.name in mail_info[partner_id_id]:
									mail_info[partner_id_id][record.product_id.name] = [record.name]
								else:
									if record.name not in mail_info[partner_id_id][record.product_id.name]:
										mail_info[partner_id_id][record.product_id.name].append(record.name)

		for partner in mail_info.keys():
			res_partner = self.env['res.partner'].browse(partner)
			mail_from = self.env.user.email
			mail_to = res_partner.email

			body = f"""Hello {res_partner.name},<br>
						<p>Your Following product(s) will expire on {expiration_date or ''}</p>
						<table style="padding: 8px; border: 1px solid black; border-collapse: collapse;">
							<th style="padding: 8px; border: 1px solid black; border-collapse: collapse; padding="">Product</th>
							<th style="padding: 8px; border: 1px solid black; border-collapse: collapse;">Serial Number(s)</th>
							"""
			for product in mail_info[partner].keys():
				body += f"""<tr style="padding: 8px; border: 1px solid black; border-collapse: collapse;">
								<td style="padding: 8px; border: 1px solid black; border-collapse: collapse;">{product}</td>
									"""
				serials = ", ".join(mail_info[partner][product])
				body += f"""<td style="padding: 8px; border: 1px solid black; border-collapse: collapse;"> {serials}</td></tr>"""
			body += """</table>"""
			mails = {
				'subject': "Product Expiration Alert",
				'email_from': mail_from,
				'email_to': mail_to,
				'body_html': body,
				'auto_delete': False,
			}
			mail = self.env['mail.mail'].create(mails)
			mail.send()
