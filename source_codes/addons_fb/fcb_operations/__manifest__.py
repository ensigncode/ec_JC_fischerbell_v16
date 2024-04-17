# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
	'name': 'FCB Operation',
	'version': '16.0.0.1',
	'category': 'stock',
	'summary': '',
	'website': '',
	'depends': [
		'base',
		'stock',
		'sale',
		'purchase',
		'sale_purchase',
	],
	'data': [
		"data/email_template_alert_reminder.xml",
		"data/email_alert_temp_sale_person.xml",
		"data/replenish_stock_notification_template.xml",
		"data/ir_cron.xml",
		"views/product_template.xml",
		"views/sale_order_view.xml",
		"views/stock_picking_views.xml",
		"views/res_partner_views.xml",
		"views/stock_location_views.xml",
		"reports/packing_label_report.xml",
	],
	'demo': [
	],

	'installable': True,
	'auto_install': False,
	'application': True,
	'license': 'LGPL-3',
}
