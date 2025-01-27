# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_round

class StockMoveWizard(models.TransientModel):
    _name = 'stock.move.wizard'

    move_line_ids = fields.One2many('stock.move.line.wizard', 'move_id',  string = 'Lines')

    def action_send_mail_manager(self):
        purchase_group = self.env.ref('purchase.group_purchase_user', raise_if_not_found=False)
        purchase_users = purchase_group.users if purchase_group else self.env['res.users']

        picking_id = self.env['stock.picking'].browse(self._context.get('active_id'))
        low_stock_products = []
        for line in self.move_line_ids:
            if line.line_qty:
                low_stock_products.append(f"{line.product_id.display_name}: Exceed Qty {line.line_qty},")

        purchase_emails = ", ".join([user.email for user in purchase_users if user.email])
        if low_stock_products and purchase_emails:
            subject = _(f"Exceed Po Qty")
            body = _(
                    f"Dear Purhase Manager,<br/><br/>"
                    f"The following products have exceeded the quantity and require a Purchase Order::<br/><ul>{''.join(f'<li>{p}</li>' for p in low_stock_products)}</ul><br/>"
                    f"A purchase order has been created for the required quantities. Please review it.<br/>"
                    f"Please review and take necessary actions.<br/><br/><br/>"
                    f"Thank You."
            )

            mail_values = {
                'subject': subject,
                'body_html': body,
                'email_to': purchase_emails,
                'email_from': self.env.user.email or self.env.company.email,
            }
            email_log_message = _(
                f"<b>Subject:</b> {mail_values['subject']}<br/>"
                f"<br/>{mail_values['body_html']}"
            )
            picking_id.message_post(body=email_log_message, subtype_xmlid='mail.mt_note')
            picking_id.is_exceed_picking = True
            self.env['mail.mail'].create(mail_values).send()
        return True




class StockMoveLineWizard(models.TransientModel):
    _name = 'stock.move.line.wizard'

    product_id = fields.Many2one('product.product')
    move_id = fields.Many2one('stock.move.wizard')
    move_qty = fields.Float('Demand Qty')
    line_qty = fields.Float('Required Qty')
    total_qty = fields.Float('Total Quantity', compute='_compute_total_qty')

    @api.depends('line_qty')
    def _compute_total_qty(self):
        for record in self:
            record.total_qty = record.line_qty + record.move_qty



