from odoo import models, fields, api

class RejectReasonWizard(models.TransientModel):
    _name = 'reject.reason.wizard'
    _description = 'Reject Reason Wizard'

    reason = fields.Text(string="Reason", required=True)

    def action_reject(self):
        # Get the context to find the purchase order line to reject
        purchase_order_line_id = self.env.context.get('active_id')
        purchase_order_line = self.env['purchase.order.line'].browse(purchase_order_line_id)
        
        if purchase_order_line:
            # Log the reason in the purchase order as a note
            message = f"Purchase Order Line Rejected: {self.reason}"
            purchase_order_line.order_id.message_post(body=message)

            # Remove the line
            purchase_order_line.unlink()
