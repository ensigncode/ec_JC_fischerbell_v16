
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class PurchaseOrderCancellationWizard(models.TransientModel):
    _name = 'purchase.order.cancellation.wizard'
    _description = 'Purchase Order Cancellation Wizard'

    reason = fields.Text(string="Cancellation Reason", required=True)
    purchase_order_id = fields.Many2one('purchase.order',string="Purchase Order")

    def submit_request(self):
        if not self.reason:
            raise UserError("You must provide a reason for cancellation.")
        if self.purchase_order_id :
            self.purchase_order_id.write({
                    'past_state' : self.purchase_order_id.state,
                    'state': 'cancel_approval',
                    'cancel_request_by': self.env.user.id,
                    'cancellation_reason' : self.reason,
                    
                })
        
        purchase_manager_group=self.env.ref('fischerbell_custom.group_purchase_order_approver')
        group_users = purchase_manager_group.users
        mail_template=self.env.ref('fischerbell_custom.email_template_cancellation_approval_template')
        recipients = ','.join(user.partner_id.email for user in group_users if user.partner_id.email)
        
        if mail_template:
            mail_template.email_to = recipients
            mail_template.send_mail(self.id, force_send=True)
        
        self.env['mail.activity'].sudo().create({
                'res_model_id': self.env.ref('purchase.model_purchase_order').id,
                'res_id': self.purchase_order_id.id,
                'user_id': self.env.user.id,
                'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                'summary': _('Cancellation Approval of RFQ : %s' % self.purchase_order_id.name),
                'note': _('<span>Hello, <b>%s</b>, just a quick reminder to review and approve the pending RFQ Cancellation <b>%s</b>.</br> Thanks!')%(self.env.user.name, self.purchase_order_id.name)
            })
        return {'type': 'ir.actions.act_window_close'}
