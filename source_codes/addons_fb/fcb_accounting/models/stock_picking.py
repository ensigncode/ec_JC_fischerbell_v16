# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api,  _


class Picking(models.Model):
    _inherit = "stock.picking"

    def write(self, vals):
        res = super(Picking, self).write(vals)
        context = {}

        if self and "date_done" in vals and vals['date_done']:
            stock_managers = self.env.ref('stock.group_stock_manager').users
            email_template = self.env.ref('fcb_accounting.mail_template_data_product_stock_confirmation')
            for picking in self:
                for user in stock_managers:
                    email_values = {
                        'email_to': user.email,
                        'subject': 'Stock Picking Validated',
                        'auto_delete': True,
                    }
                    context.update({
                        'user': user.name,
                    })
                    email_template.with_context(**context).send_mail(picking.id, force_send=False, raise_exception=True,
                                                                     email_values=email_values)
        return res