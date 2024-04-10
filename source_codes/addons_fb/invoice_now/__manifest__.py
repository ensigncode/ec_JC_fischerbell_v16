# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'FCB Invoice Now',
    'version': '16.0.0.1',
    'category': 'Accounting/Accounting',
    'summary': 'Data Sync with Datapost Peppol',
    'website': 'Data Sync with Datapost Peppol',
    'depends': [
                'account_edi',
                'account_edi_ubl_cii',
                'l10n_sg',
            ],
    'data': [
        'security/ir.model.access.csv',
        "data/ubl_20_templates.xml",
        "data/ir_cron.xml",
        "wizard/send_invoice_now_wizard_view.xml",
        "wizard/send_invoice_views.xml",
        'views/account_move_views.xml',
        'views/invoice_now_confiuration.xml',
        "views/res_partner_views.xml",
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
}