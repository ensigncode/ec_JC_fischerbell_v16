from odoo import api, fields, models
from odoo.addons.base.models.res_partner import WARNING_MESSAGE, WARNING_HELP


class ResPartner(models.Model):
    _inherit = 'res.partner'
    code = fields.Char()
    @api.model
    def default_get(self, fields):
        res = super(ResPartner, self).default_get(fields)
        res.update({
            'reminder_date_before_receipt':1,
        })
        return res

