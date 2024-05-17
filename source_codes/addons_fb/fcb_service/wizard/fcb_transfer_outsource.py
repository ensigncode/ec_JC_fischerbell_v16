from odoo import fields, models, api, _
from datetime import datetime


class FcbOutsourceLocation(models.TransientModel):
    _name = 'fcb.outsource.location'
    _description = 'Location'

    warehouse_id = fields.Many2one('stock.warehouse', string='Source Warehouse')
    destination_warehouse_id = fields.Many2one('stock.warehouse')
    src_location_id = fields.Many2one('stock.location', string='Source Location')
    dest_location_id = fields.Many2one('stock.location', string='Destination Location', required=True)
    ticket_id = fields.Many2one('helpdesk.ticket', )
    product_id = fields.Many2one('product.product', )
    location_ids = fields.Many2many('stock.location')
    to_destination = fields.Selection([
        ('to_fcb', 'To FCB'),
        ('direct_to_c', 'To customer'),

    ],)
    pick_up = fields.Selection([
        ('pc_driver', "Pickup by Driver"),
        ('pc_supplier', "Pickup by Supplier"),
    ],)
    outsource_service = fields.Selection([
        ('to_fcb', 'Salesman/Driver picks item from customer and brings to FCB > FCB will send item to supplier'),
        ('d_to_supplier', 'Salesman/Driver picks item from customer and brings to Supplier location'),
        ('direct_to_c', 'Salesperson will go to customer location for service'),
    ])
    @api.model
    def default_get(self, default_fields):
        ticket = self.env['helpdesk.ticket'].browse(self._context.get('active_ids'))
        res = super(FcbOutsourceLocation, self).default_get(default_fields)
        res['ticket_id'] = ticket.id
        res['product_id'] = ticket.product_id.id
        res['outsource_service'] =ticket.outsource_service
        locations = self.env['stock.location'].search([]).filtered(lambda x: x.location_id.name == 'Van')
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

    def action_create_outsource_transfer(self):
        '''to_fcb >> Salesman/Driver picks item from customer and brings to FCB > FCB will send item to supplier'''

        if self.ticket_id.outsource_service == 'to_fcb':
            # src:partner
            # dest:van .fcb
            line_vals_list = []
            for sl in self.ticket_id.service_line:
                line_vals_list.append((0, 0, {
                    'name': 'Driver Pickup',
                    'product_id': sl.product_id.id,
                    'product_uom_qty': sl.product_uom_qty,
                    'product_uom': self.env.ref('uom.product_uom_unit').id,
                    'location_id': self.env.ref('stock.stock_location_customers').id,
                    'location_dest_id': self.dest_location_id.id,
                }))
            pick_in = self.env['stock.picking'].create({
                # 'name': 'Driver Pickup',
                'partner_id': self.ticket_id.partner_id.id,
                'picking_type_id': self.env.ref('stock.picking_type_in').id,
                'location_id': self.env.ref('stock.stock_location_customers').id,
                'location_dest_id': self.dest_location_id.id,
                'ticket_id': self.ticket_id.id,
                'move_ids': line_vals_list})
            pick_in.action_confirm()

            # src: fcb
            # dest: vendor
            po = self.env['purchase.order'].create({
                "partner_id": self.ticket_id.vender_id.id,
                "picking_type_id": self.env.ref('stock.picking_type_in').id,
                "mail_sended": True,
                "request_delivery_date": datetime.now(),
                "estimated_delivery_date": datetime.now(),
                "ticket_id": self.ticket_id.id,
                "origin":self.ticket_id.name,
                "order_line": [(0, 0, {
                    'product_id': self.ticket_id.product_service_id.product_variant_id.id,
                    'name': self.ticket_id.product_service_id.product_variant_id.name,
                    'product_qty': 1.0,
                    'price_unit': 1,
                    'taxes_id': False,
                })],
            })
            po.button_confirm()

            delivery = po.picking_ids
            line_vals_list2 = []
            for sl in self.ticket_id.service_line:
                line_vals_list2.append((0, 0, {
                    'name': ' Unload to Warehouse ',
                    'product_id': sl.product_id.id,
                    'product_uom_qty': sl.product_uom_qty,
                    'product_uom': self.env.ref('uom.product_uom_unit').id,
                    'location_id': self.dest_location_id.id,
                    'location_dest_id': self.env.ref('fcb_service.location_repair').id
                }))
            pick_from_fcb = self.env['stock.picking'].create({
                # 'name': 'Unload to Warehouse',
                "partner_id": self.ticket_id.vender_id.id,
                'picking_type_id': self.env.ref('stock.picking_type_in').id,
                'location_id': self.dest_location_id.id,
                'location_dest_id': self.env.ref('fcb_service.location_repair').id,

                'ticket_id': self.ticket_id.id,
                'move_ids': line_vals_list2})

            pick_from_fcb.action_confirm()
            line_vals_list3 = []
            for sl in self.ticket_id.service_line:
                line_vals_list3.append((0, 0, {
                    'name': ' Unload to Warehouse ',
                    'product_id': sl.product_id.id,
                    'product_uom_qty': sl.product_uom_qty,
                    'product_uom': self.env.ref('uom.product_uom_unit').id,
                    'location_id': self.env.ref('fcb_service.location_repair').id,
                    'location_dest_id': self.dest_location_id.id,
                }))
            if self.to_destination == 'to_fcb':
                vender_to_fcb = self.env['stock.picking'].create({
                    # 'name': 'Unload to Warehouse',
                    "partner_id": self.ticket_id.user_id.partner_id.id,
                    'picking_type_id': self.env.ref('stock.picking_type_in').id,
                    'location_id': self.env.ref('fcb_service.location_repair').id,
                    'location_dest_id': self.dest_location_id.id,
                    'ticket_id': self.ticket_id.id,
                    'move_ids': line_vals_list3})

                vender_to_fcb.action_confirm()
            # res = delivery.button_validate()
            # src: vendor
            # dest: fcb / customer
            line_vals_list4 = []
            for sl in self.ticket_id.service_line:
                line_vals_list4.append((0, 0, {
                    'name': ' Unload to Warehouse ',
                    'product_id': sl.product_id.id,
                    'product_uom_qty': sl.product_uom_qty,
                    'product_uom': self.env.ref('uom.product_uom_unit').id,
                    'location_id': self.env.ref(
                        'fcb_service.location_repair').id if self.to_destination == 'direct_to_c' else self.dest_location_id.id,
                    'location_dest_id': self.env.ref('stock.stock_location_customers').id,
                }))
            pick_output = self.env['stock.picking'].create({
                # 'name': 'Unload to Warehouse',
                'partner_id': self.ticket_id.partner_id.id,
                'picking_type_id': self.env.ref('stock.picking_type_out').id,
                'location_id': self.env.ref(
                    'fcb_service.location_repair').id if self.to_destination == 'direct_to_c' else self.dest_location_id.id,
                'location_dest_id': self.env.ref('stock.stock_location_customers').id,
                'ticket_id': self.ticket_id.id,
                'move_ids': line_vals_list4})

            pick_output.action_confirm()

            # d_to_supplier >> Salesman/Driver picks item from customer and brings to Supplier location
        if self.ticket_id.outsource_service == 'd_to_supplier':
            line_vals_list = []
            for sl in self.ticket_id.service_line:
                line_vals_list.append((0, 0, {
                    'name': 'Driver Pickup',
                    'product_id': sl.product_id.id,
                    'product_uom_qty': sl.product_uom_qty,
                    'product_uom': self.env.ref('uom.product_uom_unit').id,
                    'location_id': self.env.ref('stock.stock_location_customers').id,
                    'location_dest_id': self.env.ref('fcb_service.location_repair').id,
                }))
            pick_in = self.env['stock.picking'].create({
                # 'name': 'Driver Pickup',
                'partner_id': self.ticket_id.partner_id.id,
                'picking_type_id': self.env.ref('stock.picking_type_in').id,
                'location_id': self.env.ref('stock.stock_location_customers').id,
                'location_dest_id': self.env.ref('fcb_service.location_repair').id,
                'ticket_id': self.ticket_id.id,
                'pick_up': self.pick_up,
                'move_ids': line_vals_list})
            pick_in.action_confirm()

            po = self.env['purchase.order'].create({
                "partner_id": self.ticket_id.vender_id.id,
                "picking_type_id": self.env.ref('stock.picking_type_in').id,
                "mail_sended": True,
                "request_delivery_date": datetime.now(),
                "estimated_delivery_date": datetime.now(),
                "ticket_id": self.ticket_id.id,
                "origin": self.ticket_id.name,
                "order_line": [(0, 0, {
                    'product_id': self.ticket_id.product_service_id.product_variant_id.id,
                    'name': self.ticket_id.product_service_id.product_variant_id.name,
                    'product_qty': 1.0,
                    'price_unit': 1,
                    'taxes_id': False,
                })],
            })
            po.button_confirm()

            delivery = po.picking_ids
