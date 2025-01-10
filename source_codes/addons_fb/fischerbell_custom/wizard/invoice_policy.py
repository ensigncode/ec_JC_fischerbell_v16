# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from collections import defaultdict  # Add this import
from odoo.exceptions import UserError, ValidationError



class InvoicePolicyWizard(models.TransientModel):
    _name = 'invoice.policy.wizard'


    purchase_method = fields.Selection([
        ('purchase', 'On Ordered quantities'),
        ('receive', 'On Received quantities'),
    ], string="Control Policy", help="On ordered quantities: Control bills based on ordered quantities.\n"
        "On received quantities: Control bills based on received quantities.", required=False)

    invoice_policy = fields.Selection(
        [('order', 'Ordered quantities'),
         ('delivery', 'Delivered quantities')], string='Invoicing Policy',
        help='Ordered Quantity: Invoice quantities ordered by the customer.\n'
             'Delivered Quantity: Invoice quantities delivered to the customer.')

    def _notify_supplier_of_pickup(self, purchase_id):
        """Send email notification to the supplier when collection is 'self_collection'."""
        if not purchase_id.partner_id.email:
            raise ValidationError(_("The supplier does not have an email address."))

        # Get the email template
        email_template = self.env.ref('fischerbell_custom.email_template_pickup_arranged_driver_notification_template', raise_if_not_found=False)
        if not email_template:
            raise ValidationError(_("The email template for pickup arrangement is missing. Please configure it in the system."))

        # Send the email using the template
        email_template.send_mail(purchase_id.id, force_send=True)


    def btn_confirm(self):
        product_list = []
        if self._context.get("active_model") == 'purchase.order' and self._context.get("is_purchase"):
            purchase_id = self.env["purchase.order"].search([("id", '=', self._context.get("active_id"))])
            line_ids = purchase_id.order_line.filtered(lambda x: x.product_id.detailed_type != 'service').mapped(
                'product_id').write({'purchase_method': self.purchase_method})
            purchase_id.write({'name': self.env['ir.sequence'].next_by_code('purchase.order.po')})
            purchase_id.button_confirm()
            email_template = self.env.ref('purchase.email_template_edi_purchase_done', raise_if_not_found=False)
            if email_template:
                email_template.send_mail(purchase_id.id, force_send=True)
            if purchase_id.picking_ids:
                for picking in purchase_id.picking_ids:
                    if purchase_id.collection == 'self_collection':
                        picking.update({'pick_up': 'pc_driver'})
                        self._notify_supplier_of_pickup(purchase_id)
                    elif purchase_id.collection == 'assigned_driver':   
                        picking.update({'pick_up': 'pc_supplier'})
                    else:
                        picking.update({'pick_up': ''})

        if self._context.get("active_model") == 'sale.order' and self._context.get("is_sale"):
            sale_id = self.env["sale.order"].search([("id", '=', self._context.get("active_id"))])
            line_ids = sale_id.order_line.filtered(lambda x:x.product_id.detailed_type != 'service').mapped('product_id').write({'invoice_policy':self.invoice_policy})
            sale_id.action_confirm()
            location_ids = []

            lines_not_invoiced = sale_id.order_line.filtered(lambda line: line.product_id.qty_available <= 0.0)
            lines_by_location = defaultdict(list)

            for line in lines_not_invoiced:
                remaining_qty = line.product_uom_qty
                quant_ids = self.env['stock.quant'].search(
                    [('product_id', '=', line.product_id.id), ('reserved_quantity', '=', 0.0)]
                )

                if not quant_ids:
                    continue

                for quant in quant_ids:
                    if remaining_qty <= 0:
                        break

                    location = quant.location_id
                    available_qty = quant.quantity - quant.reserved_quantity

                    qty_to_add = min(remaining_qty, available_qty)
                    if qty_to_add > 0:
                        remaining_qty -= qty_to_add
                        location_ids.append(location.name)
                        lines_by_location[location].append({
                            'line': line,
                            'qty': qty_to_add
                        })

            for location, lines_group in lines_by_location.items():
                picking_type = self.env['stock.picking.type'].search([('code', '=', 'outgoing')], limit=1)
                picking_lines = []
                for line_info in lines_group:
                    line = line_info['line']
                    qty_to_add = line_info['qty']
                    picking_lines.append((0, 0, {
                        'name': line.product_id.name,
                        'product_id': line.product_id.id,
                        'product_uom_qty': qty_to_add,
                        'product_uom': line.product_uom.id,
                        'location_id': location.id,
                        'location_dest_id': sale_id.warehouse_id.lot_stock_id.id
                    }))

                if picking_lines:
                    picking = self.env['stock.picking'].create({
                        'picking_type_id': picking_type.id,
                        'partner_id': sale_id.partner_id.id,
                        'origin': sale_id.name,
                        'sale_id': sale_id.id,
                        'location_id': location.id,
                        'location_dest_id': sale_id.warehouse_id.lot_stock_id.id,
                        'move_ids_without_package': picking_lines
                    })

                    picking.action_confirm()
        return True