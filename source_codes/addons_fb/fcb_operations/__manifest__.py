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
		'purchase',
	],
	'data': [
		"data/email_template_alert_reminder.xml",
		"data/ir_cron.xml"
	],
	'demo': [
	],

	'installable': True,
	'auto_install': False,
	'application': True,
	'license': 'LGPL-3',
}
