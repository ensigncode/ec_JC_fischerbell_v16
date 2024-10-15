# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    freight_charge_id = fields.Many2one('product.product', 'Freight Charge')
    return_time = fields.Integer('Return Time')
    delivery_lead_time_days = fields.Integer(
        string='Delivery Lead Time (Days)',
        config_parameter='sale_order_lead_time_notification.delivery_lead_time_days',
        default=5,
        help="Number of days to check for delivery lead time and notify managers if stock is insufficient."
    )


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
