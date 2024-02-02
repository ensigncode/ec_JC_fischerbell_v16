# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'RX Eyewear',
    'version': '16.0.0.1',
    'category': 'mrp',
    'summary': '',
    'website': '',
    'depends': ['website','sale','report_xlsx','stock',"sale_purchase"],
    'data': [
        "security/ir.model.access.csv",
        "views/optician_detail_views.xml",
        "views/optician_detail_template.xml",
        "views/product_template_views.xml",
        "views/optician_detail_portal_template.xml",
        "views/sale_order_views.xml",
        "views/purchase_order_views.xml",
        "views/menus.xml",
    ],
    'demo': [
    ],
  'assets': {
        'web.assets_frontend': [
            'rx_eyewear/static/src/scss/optician_detail.scss',
            'rx_eyewear/static/src/js/optician_detail.js',
        ],
       
    },
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
}