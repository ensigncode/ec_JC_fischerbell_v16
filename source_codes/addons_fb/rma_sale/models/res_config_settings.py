
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    show_full_page_sale_rma = fields.Boolean(
        related="company_id.show_full_page_sale_rma",
        readonly=False,
    )
