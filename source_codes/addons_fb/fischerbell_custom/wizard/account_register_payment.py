# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, RedirectWarning
from odoo.tools.misc import formatLang, format_date



class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"


    bank_account_no = fields.Char('Bank No')
    is_bank = fields.Boolean()

    @api.onchange('payment_method_line_id')
    def onchange_paymnet_method(self):

        for record in self:
            if record.payment_method_line_id.name == 'Cheque':
                record.is_bank = True
            else:
                record.is_bank = False

    def _init_payments(self, to_process, edit_mode=False):
        records = self.env['product.template'].browse(12846 )
        import pdb
        pdb.set_trace()
        for reg in records:
            prod_new = reg.sudo().copy({'name': reg.name+' (copy)'})
            prod_new['bom_count'] = reg.bom_count
            for rec in reg.bom_ids:
                value = self.env['mrp.bom'].create({
                    'type': rec.type,
                    'product_tmpl_id': prod_new.id,
                    'product_qty': rec.product_qty,
                    'code': rec.code,
                    'company_id': rec.company_id.id,
                })
                value['bom_line_ids'] = [(0, 0, {
                    'product_id': line.product_id.id,
                    'product_qty': line.product_qty,
                    'attachments_count': line.attachments_count,
                }) for line in rec.bom_line_ids]
                print('>>>>>>>>>>>>>>>>v', value, prod_new)
        payments = super()._init_payments(to_process, edit_mode=edit_mode)
        for payment, vals in zip(payments, to_process):
                payment.write({'bank_account_no': self.bank_account_no})
        return payments