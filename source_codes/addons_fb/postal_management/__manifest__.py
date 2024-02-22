# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Postal Management',
    'version': '16.0.0.1',
    'category': '',
    'summary': '',
    'website': '',
    'depends': [
                'stock',
                'sale',
                'fleet',
            ],
    'data': [
        'security/ir.model.access.csv',
        'wizard/assgin_driver_view.xml',
        'views/postal_view.xml',
        'views/stock_picking_view.xml',
        'views/res_partner_view.xml',
        'views/sale_order_view.xml',
        'demo/demo.xml',

    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
}