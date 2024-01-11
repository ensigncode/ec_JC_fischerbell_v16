# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'FCB Spill Kit',
    'version': '16.0.0.1',
    'category': 'mrp',
    'summary': '',
    'website': '',
    'depends': [
                'mrp',
                'sale',
                'stock'
            ],
    'data': [
        "views/mrp_bom_view.xml"
    ],
    'demo': [
    ],
  
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
}