# -*- coding: utf-8 -*-

from odoo import api, models, fields


class Task(models.Model):
    _inherit = 'project.task'

    def action_print_qwb_report(self):
        return self.env.ref('industry_fsm.task_custom_report').report_action(self)
