# -*- coding: utf-8 -*-

from odoo import api, models, fields
import json
from odoo.tools import html2plaintext


class Task(models.Model):
    _inherit = 'project.task'

    product_id = fields.Many2one('product.product', string="Product")
    equipment_product_id = fields.Many2one('product.product', string="Product")
    equipment_database_product = fields.Char("Equipment Database Product", compute="_get_equipment_database_domain")
    equipment_database_serial = fields.Char("Equipment Database Serial", compute="_get_equipment_database_domain")
    equipment_database_id = fields.Many2one("equipment.service","Serial Number")
    service_date = fields.Datetime("Service Date")
    next_service_date = fields.Datetime("Next Service Date")


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
        report_action = self.env.ref('fcb_service.calibration_report')
        return report_action.report_action(self)

    def _generate_qr_code(self):
        formatted_string = ''
        for record in self:
            service_ids = self.search([('partner_id', '=', record.partner_id.id)])
            for service in service_ids:
                name = service.name
                status = service.stage_id.name
                equipment_sku = record.product_id.default_code if record.product_id.default_code else ''
                equipment = record.product_id.name
                service_date = record.service_date
                next_service_date = record.next_service_date
                formatted_string += "Name: {:<20} Status: {} SKU/Model No.: {} Equipment: {} Service Date: {}  Next Service Date:{}".format(name, status, equipment_sku, equipment, service_date, next_service_date) + '\n\n\n'
        plain_text = html2plaintext(formatted_string).strip()
        return plain_text
