# -*- coding: utf-8 -*-
from odoo import models
FORMAT_CODES = [
    'facturx_1_0_05',
    'ubl_bis3',
    'ubl_de',
    'nlcius_1',
    'efff_1',
    'ubl_2_1',
    'ubl_a_nz',
    'ubl_sg',
]


class AccountEdiXmlUBLSG(models.AbstractModel):
    _inherit = "account.edi.format"

    def _get_move_applicability(self, move):
        # EXTENDS account_edi
        self.ensure_one()
        if self.code not in FORMAT_CODES:
            return super()._get_move_applicability(move)

        if self._is_ubl_cii_available(move.company_id) and move.move_type in ('out_invoice', 'out_refund', 'in_invoice'):
            return {'post': self._ubl_cii_post_invoice}