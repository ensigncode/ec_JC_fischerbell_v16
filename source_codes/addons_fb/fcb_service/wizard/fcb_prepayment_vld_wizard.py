from odoo import fields, models, api, _


class FcbPrepaymentValidation(models.TransientModel):
    _name = 'fcb.prepayment.validation'
    _description = 'Prepayment Validation'


    def action_submit(self):
        pass
