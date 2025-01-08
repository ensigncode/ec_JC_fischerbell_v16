
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class StockPickingCancellationWizard(models.TransientModel):
    _name = 'stock.picking.cancellation.wizard'
    _description = 'Transfer Cancellation Wizard'

    reason = fields.Text(string="Cancellation Reason", required=True)
    stock_picking_id = fields.Many2one('stock.picking',string="Transfer")

    def submit_request(self):
        if not self.reason:
            raise UserError("You must provide a reason for cancellation.")
        if self.stock_picking_id :
            self.stock_picking_id.write({
                'past_state' : self.stock_picking_id.state
            })
            self.stock_picking_id.write({
                    'state': 'cancel_approval',
                    'cancel_request_by': self.env.user.id,
                    'cancellation_reason' : self.reason,
                    
                })
        
        purchase_manager_group=self.env.ref('fischerbell_custom.group_purchase_order_approver')
        group_users = purchase_manager_group.users
        mail_template=self.env.ref('fischerbell_custom.email_template_picking_cancellation_approval_template')
        recipients = ','.join(user.partner_id.email for user in group_users if user.partner_id.email)
        
        if mail_template:
            mail_template.email_to = recipients
            mail_template.send_mail(self.env.user.id, force_send=True)
        
        self.env['mail.activity'].sudo().create({
                'res_model_id': self.env.ref('stock.model_stock_picking').id,
                'res_id': self.stock_picking_id.id,
                'user_id': self.env.user.id,
                'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                'summary': _('Cancellation Approval of RFQ : %s' % self.stock_picking_id.name),
                'note': _('<span>Hello, <b>%s</b>, just a quick reminder to review and approve the Transfer Cancellation <b>%s</b>.</br> Thanks!')%(self.env.user.name, self.stock_picking_id.name)
            })
        return {'type': 'ir.actions.act_window_close'}
