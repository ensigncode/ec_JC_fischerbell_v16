from odoo import fields, models, api, _


class FcbLocation(models.TransientModel):
    _name = 'fcb.location'
    _description = 'Location'

    warehouse_id = fields.Many2one('stock.warehouse', string='Source Warehouse')
    destination_warehouse_id = fields.Many2one('stock.warehouse')
    src_location_id = fields.Many2one('stock.location', string='Source Location')
    dest_location_id = fields.Many2one('stock.location',string='Destination Location',required=True)
    ticket_id = fields.Many2one('helpdesk.ticket', )
    product_id = fields.Many2one('product.product', )

    @api.model
    def default_get(self, default_fields):
        ticket = self.env['helpdesk.ticket'].browse(self._context.get('active_ids'))
        res = super(FcbLocation, self).default_get(default_fields)
        res['ticket_id'] = ticket.id
        res['product_id'] = ticket.product_id.id

        return res

    def action_create_transfer(self):
        pick_in = self.env['stock.picking'].create({
            'picking_type_id': self.env.ref('stock.picking_type_in').id,
            'location_id': self.env.ref('stock.stock_location_customers').id,
            'location_dest_id': self.dest_location_id.id,
            'ticket_id':self.ticket_id.id,
            'move_ids': [(0, 0, {
                'name':'jhfvjhcvk',
                'product_id': self.ticket_id.product_id.id,
                'product_uom_qty': 1,
                'product_uom': self.env.ref('uom.product_uom_unit').id,
                'location_id': self.env.ref('stock.stock_location_customers').id,
                'location_dest_id': self.dest_location_id.id,
            })],
        })

        pick_output = self.env['stock.picking'].create({
            'picking_type_id': self.env.ref('stock.picking_type_out').id,
            'location_id':  self.dest_location_id.id,
            'location_dest_id':149,
            'ticket_id': self.ticket_id.id,
            'move_ids': [(0, 0, {
                'name': 'jhfvjhcvk',
                'product_id': self.ticket_id.product_id.id,
                'product_uom_qty': 1,
                'quantity_done':1,
                'product_uom': self.env.ref('uom.product_uom_unit').id,
                'location_id':149,
                'location_dest_id':  self.dest_location_id.id,
            })],
        })
        pick_in.action_confirm()
        pick_output.action_confirm()


