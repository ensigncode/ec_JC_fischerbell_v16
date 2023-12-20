from odoo import _, api, models, fields


class PurchaseOrderWizard(models.TransientModel):
    _name = "purchase.order.wizard"
    _description = "Purchase Order Wizard"


    purchase_order_type = fields.Selection([('rfq', 'Requests for Quotation'),
                                         ('po', 'Purchase Orders')], string="Purchase Order Type", required=True, default='rfq')

    def action_select_purchase_order(self):
        if self.purchase_order_type == 'rfq':
            action = self.env["ir.actions.actions"]._for_xml_id("purchase.purchase_rfq")
        else:
            action = self.env["ir.actions.actions"]._for_xml_id("purchase.purchase_form_action")
        return action

