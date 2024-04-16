# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

class ServiceWorkorder(models.Model):
    _name ="service.workorder"
    _description = "Service Workorders"

    service_id = fields.Many2one("project.task", domain="[('is_fsm', '=', True)]")
    