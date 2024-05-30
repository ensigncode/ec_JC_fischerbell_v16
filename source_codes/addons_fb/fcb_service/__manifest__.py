# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'FCB Service',
    'version': '16.0.0.1',
    'category': 'Servicres/Field Service',
    'summary': 'FCB Service',
    'website': '',
    'depends': [
        'industry_fsm', 'sale', 'stock', 'industry_fsm_sale',
        'helpdesk','purchase','industry_fsm_report','portal_signature'
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/fischerbell_security.xml',
        'data/service_email_reminder.xml',
        'data/stock_demo.xml',
        'data/workshhet_data.xml',
        'data/project_task_seq.xml',
        'data/helpdesk_data.xml',
        'views/service_views.xml',
        'views/product_template_view.xml',
        'views/project_task_view.xml',
        'reports/custome_footer.xml',
        'views/equipment_service_views.xml',
        'views/helpdesk_ticket.xml',
        'views/stock_picking_view.xml',
        'views/sale_order_view.xml',
        'views/res_company_view.xml',
        'views/purchase_order_view.xml',
        'views/transfer_portal.xml',
        'wizard/transfer_details_views.xml',
        'wizard/transfer_return_details_views.xml',
        'wizard/transfer_outsource_views.xml',
        'wizard/transfer_int_details_views.xml',
        'reports/fischerbell_medical_oxy_resu.xml',
        'reports/fischerbell_instrumental_evaluation.xml',
        'reports/fischerbell_eba_service.xml',
        'reports/fischerbell_hazmat_suit_inspection.xml',
        'reports/fischerbell_life_jacket_inspection.xml',
        'reports/fischerbell_personal_fall_protection.xml',
        'reports/fischerbell_calibration.xml',
        'reports/fischerbell_scba_mask_inspection.xml',
        'reports/fischerbell_paper_test.xml',
        'reports/fischerbell_cert_team_inspection.xml',
        'reports/fischerbell_service_qr_code.xml',

    ],
    'demo': [
    ],
    "assets": {
        "web.assets_backend": [
            "/fcb_service/static/src/js/*.js",
        ],
    },

    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
}
