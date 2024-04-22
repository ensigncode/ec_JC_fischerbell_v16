# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from datetime import timedelta


class EquipmentService(models.Model):
    _name = "equipment.service"
    _rec_name = 'partner_id'


    partner_id = fields.Many2one('res.partner',string="Customer ")
    product_id = fields.Many2one('product.product',string="Product")
    delivered_date = fields.Datetime(string="Delivery Date")
    lot_id = fields.Many2one('stock.lot',string="Lot/Serial Number")
    serial_number= fields.Float(string='Serial Number')
    so_ref = fields.Char(string='So Ref')
    categ_id = fields.Many2one('product.category', 'Product Category')
    expire_date = fields.Datetime('Expire Date')
    service_date = fields.Datetime('service Date')
    service_reminder_date = fields.Datetime('service Reminder Date')

    def _send_reminder_emails(self):
    equipment_records = self.env['equipment.service'].search([])
    for record in equipment_records:
        if record.service_reminder_date and record.partner_id:  # Check if service reminder date and partner are set
            today = fields.Date.today()
            if record.service_reminder_date.date() == today:
                template = self.env.ref('fcb_service.email_template_service_reminder')
                template_values = {
                    'email_from': self.env.user.email,
                    'email_to': record.partner_id.email,
                }
                template.sudo().send_mail(record.id, force_send=True, email_values=template_values)

    @api.onchange('product_id')
    def onchange_product_id(self):
        domain = []
        if self.product_id:
            domain = [('product_id', '=', self.product_id.id)]
            self.categ_id = self.product_id.categ_id.id or False
            if self.delivered_date:
                service_time = timedelta(days=self.product_id.service_time)
                reminder_time = timedelta(days=self.product_id.service_reminder_days)
                self.service_date = self.delivered_date + service_time
                self.service_reminder_date = self.service_date - reminder_time
        else:
            self.categ_id = False
            self.service_date = False
            self.service_reminder_date = False
        return {'domain': {'lot_id': domain}}

    @api.onchange('lot_id')
    def onchange_lot_id(self):
        for record in self:
            lot_id = self.env['stock.lot'].search([('id', '=', record.lot_id.id)])
            record.product_id = lot_id.product_id.id or False
            record.categ_id = lot_id.product_id.categ_id.id or False
            record.expire_date = lot_id.expiration_date or False





