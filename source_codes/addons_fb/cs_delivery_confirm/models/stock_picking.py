# -*- coding: utf-8 -*-

import datetime
from odoo.http import request
from dateutil.relativedelta import relativedelta
from odoo import models, api, fields


class StockPicking(models.Model):
    _inherit = 'stock.picking'

   
    upload_images = fields.Many2many(
        comodel_name = 'ir.attachment',
        relation = 'stock_picking_ir_attachment'
        )
