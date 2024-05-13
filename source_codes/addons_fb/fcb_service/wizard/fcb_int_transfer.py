from odoo import fields, models, api, _


class FcbIntLocation(models.TransientModel):
    _name = 'fcb.int.location'
    _description = 'Location'

    warehouse_id = fields.Many2one('stock.warehouse', string='Source Warehouse')
    destination_warehouse_id = fields.Many2one('stock.warehouse')
    src_location_id = fields.Many2one('stock.location', string='Source Location')
    dest_location_id = fields.Many2one('stock.location', string='Destination Location', required=True)
    ticket_id = fields.Many2one('helpdesk.ticket', )
    product_id = fields.Many2one('product.product', )
    location_ids = fields.Many2many('stock.location')

    @api.model
    def default_get(self, default_fields):
        ticket = self.env['helpdesk.ticket'].browse(self._context.get('active_ids'))
        res = super(FcbIntLocation, self).default_get(default_fields)
        res['ticket_id'] = ticket.id
        res['product_id'] = ticket.product_id.id
        locations = self.env['stock.location'].search([]).filtered(lambda x:x.location_id.name == 'Van')
        if 'location_ids' in default_fields:
            if locations:
                if len((locations)) == 1:
                    res['location_ids'] = [(6, 0, [locations[0].id])]
                    res.update({
                        'dest_location_id': locations[0].id,
                    })
                else:
                    res['location_ids'] = [(6, 0, [t.id for t in locations])]
            else:
                res['dest_location_id'] = False
        return res

    def action_create_int_transfer(self):
        line_vals_list = []
        for sl in self.ticket_id.service_line:
            line_vals_list.append((0,0,{
                'name': 'Driver Pickup',
                'product_id': sl.product_id.id,
                'product_uom_qty': sl.product_uom_qty,
                'quantity_done': sl.product_uom_qty,
                'product_uom': self.env.ref('uom.product_uom_unit').id,
                'location_id': self.env.ref('fcb_service.location_repair').id,
                'location_dest_id': self.dest_location_id.id,
            }))
        pick_in = self.env['stock.picking'].create({
            # 'name': 'Driver Pickup',
            'partner_id': self.ticket_id.partner_id.id,
            'picking_type_id': self.env.ref('stock.picking_type_in').id,
            'location_id':self.env.ref('fcb_service.location_repair').id,
            'location_dest_id': self.dest_location_id.id,
            'ticket_id': self.ticket_id.id,
            'move_ids': line_vals_list})

        line_valsout_list = []
        for sl in self.ticket_id.service_line:
            line_valsout_list.append((0,0,{
                'name': ' Unload to Warehouse ',
                'product_id': sl.product_id.id,
                'product_uom_qty': sl.product_uom_qty,
                'product_uom': self.env.ref('uom.product_uom_unit').id,
                'location_id': self.dest_location_id.id,
                'location_dest_id': self.env.ref('stock.stock_location_output').id,
            }))

        pick_output = self.env['stock.picking'].create({
            # 'name': 'Unload to Warehouse',
            'partner_id': self.ticket_id.partner_id.id,
            'picking_type_id': self.env.ref('stock.picking_type_out').id,
            'location_id': self.dest_location_id.id,
            'location_dest_id':  self.env.ref('stock.stock_location_output').id,
            'ticket_id': self.ticket_id.id,
            'move_ids': line_valsout_list
        })
        pick_in.action_confirm()
        pick_output.action_confirm()
