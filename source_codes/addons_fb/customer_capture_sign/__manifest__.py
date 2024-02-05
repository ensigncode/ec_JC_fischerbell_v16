# Copyright 2022 CreuBlanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Customer Capture Sign",
    "summary": """
        Capture sign via url""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "",
    "website": "",
    "depends": [
        "sale_management","website"
    ],
    "data": [
        "data/esign_mail_template.xml",
        "views/sale_order_view.xml",
        "views/customer_esign_portal.xml",
    ],
    "demo": [],
     'assets': {
    },
}
