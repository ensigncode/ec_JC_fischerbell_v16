# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
	'name': 'FCB Service',
	'version': '16.0.0.1',
	'category': 'Services/Field Service',
	'summary': 'FCB Service',
	'website': '',
	'depends': [
		'industry_fsm','sale'
	],
	'data': [
		'security/ir.model.access.csv',
		'views/service_views.xml',
		'views/fischerbell_header.xml',
		'views/product_template_view.xml',
		'reports/custome_footer.xml',

	],
	'demo': [
	],

	'installable': True,
	'auto_install': False,
	'application': True,
	'license': 'LGPL-3',
}
