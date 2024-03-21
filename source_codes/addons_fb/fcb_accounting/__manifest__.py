# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'FCB Accounting',
    'version': '16.0.0.1',
    'category': 'Account',
    'summary': '',
    'website': '',
    'depends': ['account','l10n_in','account_asset','account_reports','purchase_stock',
            'stock_dropshipping'],
    'data': [
        "data/demo_data.xml",
        "data/ir_cron_data.xml",
        "data/exchange_rate_alert_mail_template.xml",
        "data/mail_template_data.xml",
        "views/res_partner_view.xml",
        "views/cash_flow_report.xml",
        "views/account_asset_views.xml",
        "views/purchase_views.xml",
    ],
    'demo': [
    ],
  
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
}