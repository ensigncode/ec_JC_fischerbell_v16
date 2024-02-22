# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Portal Signature',
    'version': '16.0.0.1',
    'category': '',
    'summary': '',
    'website': '',
    'depends': ['website'],
    'data': [
    'views/portal_signature_template.xml'
        
    ],
    'demo': [
    ],
     'assets': {
        'web.assets_frontend': [
            'portal_signature/static/src/js/pop_signature_model.js',
        ],
        },
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
}