from odoo import _, api, models, fields


class SaleOrderApprovalWizard(models.TransientModel):
    _name = "sale.order.approval.wizard"
    _description = "Sale Order Approval Wizard"

    order_id = fields.Many2one('sale.order', default=lambda self: self.env.context.get('active_id'))
    operation_type = fields.Selection([
        ("confirm", "Confirm Order"),
        ("send_mail", "Send by Email"),
        ("approve", "Approve Order")],
        required=True,
        default="approve",
    )

    def action_perform_operation(self):
        context = self.env.context
        print(context,"-----CONTEXT......")
        if self.operation_type == "confirm":
            self.order_id.with_context(context).approval_order()
        elif self.operation_type == 'approve':
            self.order_id.write({
                'approval_state': 'approved'
            })
        else:
            return self.order_id.with_context(context).action_quotation_send()
