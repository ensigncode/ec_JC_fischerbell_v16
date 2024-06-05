# -*- coding: utf-8 -*-

{
    'name': "Fit test training",
    'category': 'Website',
    'version': '16.0.0.0.0',
    'summary': """
        Customers of FCB to do fit test or training is a template where customers want to book fit test or training and 
        the sales team can email this template to customers and based on the information keyed in, it will autopopulated in the sales module
    """,
    'author': 'EnsignCode Solutions',
    'company': 'EnsignCode Solutions',
    'maintainer': 'EnsignCode Solutions',
    'website': "https://www.ensigncode.com",
    'depends': ['base', 'website', 'sale'],
    'data': [
        'security/ir.model.access.csv',
        'data/website_data.xml',
        'data/mail_template_data.xml',
        'data/training_seq.xml',
        'views/fittest_training_template.xml',
        'views/fit_test_training_views.xml',
        'report/fit_test_certificate_report.xml',
        'report/fit_test_certificate_template.xml',
    ],
    'auto_install': False,
    'installable': True,
    'application': False,
}