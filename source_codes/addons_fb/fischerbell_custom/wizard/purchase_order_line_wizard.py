from odoo import models, fields, api

class RejectReasonWizard(models.TransientModel):
    _name = 'reject.reason.wizard'
    _description = 'Reject Reason Wizard'

    reason = fields.Text(string="Reason", required=True)

    def action_reject(self):
        if self._context.get('is_purchase'):
            order_id = self.env['purchase.order'].browse(self.env.context.get('purchase_id'))
            order_id.write({
                    'state': 'reject',
                    'approval_state': 'reject',
                    'reviewed_by': self.env.user.id,
                    'reject_reason': self.reason
                })
            return True
        # Get the context to find the purchase order line to reject
        purchase_order_line_id = self.env.context.get('active_id')
        purchase_order_line = self.env['purchase.order.line'].browse(purchase_order_line_id)
        
        if purchase_order_line:
            # Log the reason in the purchase order as a note
            message = f"Purchase Order Line Rejected: {self.reason}"
            purchase_order_line.order_id.message_post(body=message)
            purchase_order_line.po_reason = self.reason
            purchase_order_line.approval_state = 'rejected'

            # Remove the line
            # purchase_order_line.unlink()
