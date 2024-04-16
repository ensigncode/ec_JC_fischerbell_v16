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
		'views/product_template_view.xml',
		'reports/custome_footer.xml',
		# 'reports/fischerbell_medical_oxy_resu.xml',
		# 'reports/fischerbell_instrumental_evaluation.xml',
		'reports/fischerbell_eba_service.xml',

	],
	'demo': [
	],

	'installable': True,
	'auto_install': False,
	'application': True,
	'license': 'LGPL-3',
}
