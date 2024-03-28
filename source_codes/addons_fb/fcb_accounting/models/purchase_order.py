# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def _create_picking(self):
        StockPicking = self.env['stock.picking']
        for order in self.filtered(lambda po: po.state in ('purchase', 'done')):
            if any(product.type in ['product', 'consu'] for product in order.order_line.product_id):
                order = order.with_company(order.company_id)
                for line in order.order_line:
                    if line.picking_type_id and line.picking_type_id.code:
                        picking_type_code = line.picking_type_id.code
                        dest_address_id = line.dest_address_id
                        pickings = order.picking_ids.filtered(lambda x: x.state not in ('done', 'cancel') and x.picking_type_code == picking_type_code and x.dest_address_id == dest_address_id)
                        if not pickings:
                            res = order._prepare_picking(picking_type_code, dest_address_id)
                            picking = StockPicking.with_user(SUPERUSER_ID).create(res)
                        else:
                            picking = pickings[0]
                        moves = line._create_stock_moves(picking)
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

    def _prepare_picking(self, picking_type_code, dest_address_id):
        self.ensure_one()
        if not self.group_id:
            self.group_id = self.group_id.create({
                'name': self.name,
                'partner_id': self.partner_id.id
            })
        if not self.partner_id.property_stock_supplier.id:
            raise UserError(_("You must set a Vendor Location for this partner %s", self.partner_id.name))
        picking_type = self.env['stock.picking.type'].search([('code', '=', picking_type_code), ('warehouse_id.company_id', '=', self.company_id.id)], limit=1)
        if not picking_type:
            raise UserError(_("Picking type not found for code: %s", picking_type_code))
        return {
            'picking_type_id': picking_type.id,
            'partner_id': self.partner_id.id,
            'user_id': False,
            'date': self.date_order,
            'origin': self.name,
            'location_dest_id': dest_address_id.property_stock_customer.id if dest_address_id else picking_type.default_location_dest_id.id,
            'location_id': self.partner_id.property_stock_supplier.id,
            'company_id': self.company_id.id,
        }

    @api.onchange('picking_type_id')
    def onchange_picking_type_id_custom(self):
        for line in self.order_line:
            line.picking_type_id = self.picking_type_id.id


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    picking_type_id = fields.Many2one('stock.picking.type', 'Deliver To', required=True,
                                      help="This will determine operation type of incoming shipment")

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
        return super(PurchaseOrderLine, self).create(vals)
    
    def _compute_tax_id(self):
        res = super()._compute_tax_id()
        for line in self:
            partner_id = line.order_id.partner_id
            if line.product_id and partner_id and partner_id.supplier_taxes and partner_id.l10n_in_gst_treatment == "overseas":
                line.taxes_id = [(6, 0, partner_id.supplier_taxes.ids)]
        return res

    default_location_dest_id_usage = fields.Selection(related='picking_type_id.default_location_dest_id.usage',
                                                      string='Destination Location Type',
                                                      help="Technical field used to display the Drop Ship Address",
                                                      readonly=True)
    dest_address_id = fields.Many2one('res.partner', compute='_compute_dest_address_id', store=True, readonly=False)

    @api.depends('picking_type_id')
    def _compute_dest_address_id(self):
        for po_line in self:
            po_line.dest_address_id = po_line.picking_type_id.default_location_dest_id.partner_id
