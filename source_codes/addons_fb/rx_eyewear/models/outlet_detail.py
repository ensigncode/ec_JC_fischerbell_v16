# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _

class RxEyewearOutlet(models.Model):
    _name = 'outlet.detail'

    name = fields.Char(string='Name')

  