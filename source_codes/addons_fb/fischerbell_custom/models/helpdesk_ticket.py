# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models

class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    sale_id = fields.Many2one('sale.order', string='Sale')
