# -*- coding: utf-8 -*-

from odoo import api, models, fields


class Task(models.Model):
    _inherit = 'project.task'

    def action_print_qwb_report(self):
        return self.env.ref('industry_fsm.task_custom_report').report_action(self)

    def action_report(self):
	    report_action = self.env.ref(
		    'fcb_service.calibration_report')  # Replace 'module_name' with the actual name of your module
	    return report_action.report_action(self)
