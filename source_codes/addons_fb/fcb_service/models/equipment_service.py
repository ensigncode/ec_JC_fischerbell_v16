# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from datetime import timedelta




class EquipmentService(models.Model):
    _name = "equipment.service"
    _rec_name = 'partner_id'


    partner_id = fields.Many2one('res.partner', string="Customer ")
    product_id = fields.Many2one('product.product', string="Product")
    delivered_date = fields.Datetime(string="Equipment Purchase Date")
    # lot_id = fields.Many2one('stock.lot', string="Lot/Serial Number")
    serial_number = fields.Char(string='Serial Number')
    so_ref = fields.Char(string='So Ref')
    categ_id = fields.Many2one('product.category', 'Product Category',readonly=True)
    expire_date = fields.Datetime('Expire Date')
    manufacturing_date = fields.Datetime('Manufacturing Date')
    is_inhouse_service = fields.Boolean("Is Inhouse Service ?")
    service_product_ids = fields.One2many('product.service', 'product_tmpl_id', 'Service Products',related='product_id.service_product_ids')
    is_serviceable = fields.Boolean('Is Serviceable',related='product_id.is_serviceable')
    product_variant_id = fields.Many2one('product.product', 'Products',)
    service = fields.Boolean(compute='_compute_service_date', store=True)
    reminder_date = fields.Boolean(compute='_compute_reminder_date', store=True)

    @api.depends('delivered_date', 'service_product_ids', 'service_product_ids.service_time', )
    def _compute_service_date(self):
        for record in self:
            for service in record.service_product_ids:
                if record.delivered_date:
                    service.service_date = (record.delivered_date.date() + timedelta(
                        days=service.service_time)) if record.delivered_date and service.service_time else False
                    record.service = True
                else:
                    record.service = False

    @api.depends('service_product_ids', 'service_product_ids.reminder_time')
    def _compute_reminder_date(self):
        for record in self:
            for service in record.service_product_ids:
                if record.delivered_date:
                    service.reminder_date = (service.service_date.date() - timedelta(
                        days=service.reminder_time)) if service.reminder_time else False
                    record.reminder_date = True
                else:
                    record.reminder_date = False

    def _send_reminder_emails(self):
        equipment_records = self.env['equipment.service'].search([])
        utc_now = fields.Datetime.now().astimezone(pytz.utc).date()  # Get current date in UTC
        for record in equipment_records:
            if record.service_reminder_date and record.partner_id and record.is_inhouse_service:  # Check if service reminder date and partner are set
                reminder_date = record.service_reminder_date.date()
                if reminder_date == utc_now:
                    template = self.env.ref('fcb_service.email_template_service_reminder')
                    template_values = {
                        'email_from': self.env.user.email,
                        'email_to': record.partner_id.email,
                    }
                    template.sudo().send_mail(record.id, force_send=True, email_values=template_values)

    @api.onchange('product_id','service_product_ids')
    def onchange_product_id(self):
        # if not self.service_product_ids:
        #     for product in self._origin.product_id.service_product_ids:
        #             self._origin.update({
        #                 'service_product_ids': [(0, 0, {
        #                     'product_variant_id': product.product_variant_id.id,
        #                     'equipment_id': product.equipment_id.id,
        #                     'service_date': product.service_date,
        #                     'reminder_date': product.reminder_date,
        #                     'service_time': product.service_time,
        #                     'reminder_time': product.reminder_time,
        #                 })]
        #             })
        domain = []

    def name_get(self):
        if self._context.get("model_name") == 'project.task':
            return [(rec.id, '%s' % (rec.serial_number)) for rec in self]
        else:
            return super(EquipmentService, self).name_get()


