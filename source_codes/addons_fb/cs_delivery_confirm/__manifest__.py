# -*- coding: utf-8 -*-
# Part of Odoo Module Developed by Cloudia Systems S.A.C. | http://cloudia.systems | <info@cloudia.systems>
# Copyright (c) 2024-Present Cloudia Systems S.A.C.
# See LICENSE and COPYRIGHT files for full copyright and licensing details.

{
    'name'                  :   'Confirmación Stock',
    'summary'               :   'Confirmación Stock',
    'description'           :   '''Confirm Stock''',

    'version'               :   '16.0.1.0',
    'category'              :   'Inventory',

  	'author'                : 	'EnsignCode',
  	'maintainer'            : 	'EnsignCode',
  	'support'               : 	'https://ensigncode.com/',

  	'website'               : 	'https://ensigncode.com/',

    'depends'               :   [
                                'base',
                                'stock',
                                'stock_barcode'
                                ],

    'data'                  :   [
                                'views/stock_picking.xml',
                                ],



    'sequence'              :   10,
    'application'           :   False,
    'installable'           :   True,

    'assets': {
        'web.assets_backend': [
            'cs_delivery_confirm/static/src/js/upload_files.js',
            'cs_delivery_confirm/static/src/xml/upload_files.xml',
            'cs_delivery_confirm/static/src/css/style.scss',
        ],
    },

    'license'               :  'OPL-1',
    'price'                 :  19.90,
    'currency'              :  'USD',

    'pre_init_hook'         :  'pre_init_hook',
}
