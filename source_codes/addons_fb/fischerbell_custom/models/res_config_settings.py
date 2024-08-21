# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    freight_charge_id = fields.Many2one('product.product', 'Freight Charge')
    return_time = fields.Integer('Return Time')
    note_limit = fields.Integer('Note Limit', related='company_id.note_limit', readonly=False, default=20)


    def set_values(self):
        res = super(ResConfigSettings, self).set_values()

        self.env['ir.config_parameter'].sudo().set_param('fischerbell_custom.freight_charge_id', int(self.freight_charge_id))
        self.env['ir.config_parameter'].sudo().set_param('fischerbell_custom.return_time', int(self.return_time))

        return res

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()

        freight_charge_id =  self.env['ir.config_parameter'].sudo().get_param('fischerbell_custom.freight_charge_id')
        return_time =  self.env['ir.config_parameter'].sudo().get_param('fischerbell_custom.return_time')
        res['freight_charge_id'] = int(freight_charge_id)
        res['return_time'] = int(return_time)

        return res
