# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

 
    def _prepare_picking(self):
        context = self.env.context
        if 'picking_type_code' and 'dest_address_id' and 'picking_type_id' in context:
            picking_type_code = context.get('picking_type_code')
            dest_address_id = context.get('dest_address_id')
            picking_type_id = context.get('picking_type_id')

            for order in self:
                if not order.group_id:
                    order.group_id = order.group_id.create({
                        'name': order.name,
                        'partner_id': order.partner_id.id
                    })
                if not order.partner_id.property_stock_supplier.id:
                    raise UserError(_("You must set a Vendor Location for this partner %s", order.partner_id.name))
                picking_type = self.env['stock.picking.type'].search([('code', '=', picking_type_code), ('warehouse_id.company_id', '=', order.company_id.id)], limit=1)
                if not picking_type:
                    raise UserError(_("Picking type not found for code: %s", picking_type_code))
                return {
                    'picking_type_id': picking_type_id.id,
                    'partner_id': order.partner_id.id,
                    'user_id': False,
                    'date': order.date_order,
                    'origin': order.name,
                    'location_dest_id': dest_address_id.property_stock_customer.id if dest_address_id else picking_type.default_location_dest_id.id,
                    'location_id': order.partner_id.property_stock_supplier.id,
                    'company_id': order.company_id.id,
                }
    
    def _create_picking(self):
        StockPicking = self.env['stock.picking']
        for order in self.filtered(lambda po: po.state in ('purchase', 'done')):
            if any(product.type in ['product', 'consu'] for product in order.order_line.product_id):
                order = order.with_company(order.company_id)
                for line in order.order_line:
                    if line.picking_type_id and line.picking_type_id.code:
                        picking_type_code = line.picking_type_id.code
                        dest_address_id = line.dest_address_id
                        pickings = order.picking_ids.filtered(lambda x: x.state not in ('done', 'cancel') and x.picking_type_code == picking_type_code)
                        res = order.with_context(picking_type_code = picking_type_code, dest_address_id = dest_address_id,picking_type_id = line.picking_type_id)._prepare_picking()
                        picking = StockPicking.with_user(SUPERUSER_ID).create(res)
                       
                        moves = line._create_stock_moves(picking)
                        for move in moves : 
                            move.location_dest_id = picking.location_dest_id
                        moves = moves.filtered(lambda x: x.state not in ('done', 'cancel'))._action_confirm()
                        seq = 0
                        for move in sorted(moves, key=lambda move: move.date):
                            seq += 5
                            move.sequence = seq
                        moves._action_assign()
                        forward_pickings = self.env['stock.picking']._get_impacted_pickings(moves)
                        (picking | forward_pickings).action_confirm()
                        picking.message_post_with_view('mail.message_origin_link',
                                                       values={'self': picking, 'origin': order},
                                                       subtype_id=self.env.ref('mail.mt_note').id)
        return True


    @api.onchange('picking_type_id')
    def onchange_picking_type_id_custom(self):
        for line in self.order_line:
            line.picking_type_id = self.picking_type_id.id


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.model
    def _default_picking_type(self):
        return self.order_id.picking_type_id if self.order_id and self.order_id.picking_type_id else False
    
    @api.model
    def _get_default_picking_type(self):
        picking_type = self.env['stock.picking.type'].search([('code', '=', 'incoming')], limit=1)
        if not picking_type:
            return False
        return picking_type.id

    @api.onchange('order_id')
    def _onchange_order_id(self):
        for line in self:
            if line.order_id:
                line.picking_type_id = line.order_id.picking_type_id.id or self._get_default_picking_type()

    @api.model
    def create(self, vals):
        if 'order_id' in vals and 'picking_type_id' not in vals:
            order_id = self.env['purchase.order'].browse(vals['order_id'])
            vals['picking_type_id'] = order_id.picking_type_id.id or self._get_default_picking_type()
        # if 'order_id' in vals and 'picking_type_id' in vals:
        #     order_id = self.env['purchase.order'].browse(vals['order_id'])
        #     vals['picking_type_id'] = order_id.picking_type_id.id

        return super(PurchaseOrderLine, self).create(vals)
    
    def _compute_tax_id(self):
        res = super()._compute_tax_id()
        for line in self:
            partner_id = line.order_id.partner_id
            if line.product_id and partner_id and partner_id.supplier_taxes and partner_id.l10n_in_gst_treatment == "overseas":
                line.taxes_id = [(6, 0, partner_id.supplier_taxes.ids)]
        return res
    
    @api.depends('picking_type_id')
    def _compute_dest_address_id(self):
        for po_line in self:
            self.filtered(lambda po_line: po_line.picking_type_id.default_location_dest_id.usage != 'customer').dest_address_id = False

    default_location_dest_id_usage = fields.Selection(related='picking_type_id.default_location_dest_id.usage',
                                                      string='Destination Location Type',
                                                      help="Technical field used to display the Drop Ship Address",
                                                      readonly=True)
    dest_address_id = fields.Many2one('res.partner', compute='_compute_dest_address_id', store=True, readonly=False, string="Destination Address")

    picking_type_id = fields.Many2one('stock.picking.type', 'Deliver To', 
                                        domain="['|', ('warehouse_id', '=', False), ('warehouse_id.company_id', '=', company_id)]",
                                      help="This will determine operation type of incoming shipment",default=_default_picking_type)


    