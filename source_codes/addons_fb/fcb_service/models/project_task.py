# -*- coding: utf-8 -*-

from odoo import api, models, fields
import json


class Task(models.Model):
    _inherit = 'project.task'

    product_id = fields.Many2one('product.product', string="Product")
    equipment_product_id = fields.Many2one('product.product', string="Product")
    equipment_database_product = fields.Char("Equipment Database Product", compute="_get_equipment_database_domain")
    equipment_database_serial = fields.Char("Equipment Database Serial", compute="_get_equipment_database_domain")
    equipment_database_id = fields.Many2one("equipment.service","Serial Number")


    @api.depends("partner_id")
    def _get_equipment_database_domain(self):
        for equipment in self:
            equipment_ids = self.env['equipment.service'].search([('partner_id','=', equipment.partner_id.id)])
            product_ids = [prod.id for prod in equipment_ids.mapped('product_id')]
            serial_ids = [serial.id for serial in equipment_ids]
            if serial_ids:
                equipment.equipment_database_serial = json.dumps([('id', 'in', serial_ids)])
            else:
                equipment.equipment_database_serial = json.dumps([('id', 'in', [])])
            if product_ids:
                equipment.equipment_database_product = json.dumps([('id', 'in', product_ids)])
            else:
                equipment.equipment_database_product = json.dumps([('id', 'in', [])])


    def action_print_calibration_report(self):
        return self.env.ref('fcb_service.fischerbell_calibration_task_custom_report').report_action(self)

    def action_cert_inspection_report(self):
        return self.env.ref('fcb_service.action_cert_inspection_report').report_action(self)

    def action_print_eba_service_certificate(self):
        return self.env.ref('fcb_service.eba_service_certificate').report_action(self)

    def action_print_huzmal_task_custom_report(self):
        return self.env.ref('fcb_service.action_huzmal_task_custom_report').report_action(self)

    def action_fischerbell_custom_life_jacket_report(self):
        return self.env.ref('fcb_service.action_fischerbell_custom_life_jacket_report').report_action(self)

    def action_industry_ev_task_custom_report(self):
        return self.env.ref('fcb_service.action_industry_ev_reports').report_action(self)

    def action_medical_oxy_task_custom_report(self):
        return self.env.ref('fcb_service.action_medical_oxy_task_report').report_action(self)
    def action_paper_test_task_custom_report(self):
        return self.env.ref('fcb_service.action_paper_test_task').report_action(self)
    def action_worksheet_custom_personal_fall_protection(self):
        return self.env.ref('fcb_service.action_worksheet_personal_fall_protection').report_action(self)
    def action_scba_task_custom_report(self):
        return self.env.ref('fcb_service.action_scba_task_custom_report').report_action(self)


    def action_report(self):
        report_action = self.env.ref('fcb_service.calibration_report')  # Replace 'module_name' with the actual name of your module
        return report_action.report_action(self)

