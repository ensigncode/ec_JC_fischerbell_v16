# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'FCB Activity Schedule View',
    'version': '16.0.0.0',
    'category': 'Productivity',
    'summary': 'Custom Activity Schedule View for the manager to check the pending activity for the their team members',
    'description': 'Custom Activity Schedule View for the manager to check the pending activity for the their team members.',
    'author': 'EnsignCode Solutions',
    'company': 'EnsignCode Solutions',
    'maintainer': 'EnsignCode Solutions',
    'website': "https://www.ensigncode.com",
    'depends': [
        'mail',
    ],
    'data': [
        'security/security.xml',
        'views/mail_activity_view_.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
}
