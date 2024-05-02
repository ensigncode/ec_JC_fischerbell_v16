# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models,api,fields, _

class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    picking_ticket_ids = fields.One2many('stock.picking', 'ticket_id', string='Transfers')
    purchase_ticket_ids =  fields.One2many('purchase.order', 'ticket_id', string='Purchase')
    delivery_count = fields.Integer(string='Delivery Orders', compute='_compute_picking_ticket_ids')
    purchase_count = fields.Integer(string='Purchase Orders', compute='_compute_purchase_count')
    service_priority = fields.Selection([
        ('urgent', 'Urgent'),
        ('express', 'Express'),
        ('standard', 'Standard'),
    ])
    reference_no = fields.Char(string='Order Reference', required=True,
                               readonly=True, default=lambda self: _('New'))
    date_of_request = fields.Datetime("Date of Request")
    shipping_type = fields.Selection([
        ('pickup', 'Pickup'),
        ('self_drop', 'Self Drop'),
    ])
    is_servicing = fields.Boolean(related='team_id.is_servicing')
    ticket_type = fields.Boolean(related='ticket_type_id.ticket_type')
    service_line = fields.One2many('service.order.line', 'ticket_id', string="Service Line")
    submitted_id = fields.Many2one('res.partner', string="Submitted By")
    certificate_name = fields.Char(string="Certificate Name")
    certificate_address = fields.Char(string="Certificate Address")
    task_generated = fields.Boolean(string="Task Generated")
    service_type = fields.Selection([
        ('inhouse_service', 'In House Calibration'),
        ('onsite_service', 'Onsite Calibration '),
        ('outsource_service', 'Outsource to 3rd Party Supplier'),

    ])
    outsource_service = fields.Selection([
        ('to_fcb', 'Salesman/Driver picks item from customer and brings to FCB > FCB will send item to supplier'),
        ('d_to_supplier', 'Salesman/Driver picks item from customer and brings to Supplier location'),
        ('direct_to_c', 'Salesperson will go to customer location for service'),

    ])
    product_service_id = fields.Many2one('product.template','Service For Provider', domain="[('detailed_type', '=', 'service')]")
    vender_id = fields.Many2one('res.partner', string='Vendor', tracking=True, domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", help="You can find a vendor by its Name, TIN, Email or Internal Reference.")

    @api.model
    def create(self, vals):
        if vals.get('is_servicing'):
            if vals.get('reference_no', _('New')) == _('New'):
                vals['reference_no'] = self.env['ir.sequence'].next_by_code(
                    'service_ticket_seq') or _('New')
        return super(HelpdeskTicket, self).create(vals)

    def generate_service(self):
        self.ensure_one()
        self.task_generated = True
        for line in self.service_line:
            task_name = ' | '.join([self.partner_id.name] + [line.product_id.default_code if line.product_id.default_code else line.product_id.name])
            for prod in range(int(line.product_uom_qty)):
                record = self.env['project.task'].create({
                    'project_id': self.team_id.fsm_project_id.id,
                    'name': task_name,
                    'partner_id': self.partner_id.id,
                    'product_id': line.product_id.id,
                    'helpdesk_ticket_id': self.id,
                })
        return True

    @api.depends('picking_ticket_ids','purchase_ticket_ids')
    def _compute_picking_ticket_ids(self):
        for order in self:
            order.delivery_count = len(order.picking_ticket_ids)
            order.purchase_count = len(order.purchase_ticket_ids)

    @api.depends('purchase_ticket_ids')
    def _compute_purchase_count(self):
        for order in self:
            order.purchase_count = len(order.purchase_ticket_ids)

    def action_view_transfers(self):
        """Open a new window to view transfers."""
        action = self.env["ir.actions.actions"]._for_xml_id("stock.action_picking_tree_all")
        pickings = self.picking_ticket_ids
        if len(pickings) > 1:
            action['domain'] = [('id', 'in', pickings.ids)]
        elif pickings:
            form_view = [(self.env.ref('stock.view_picking_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = pickings.id
        return action
    def action_view_purchases(self):
        """Open a new window to view transfers."""
        action = self.env["ir.actions.actions"]._for_xml_id("purchase.purchase_rfq")
        purchases = self.purchase_ticket_ids
        if len(purchases) > 1:
            action['domain'] = [('id', 'in', purchases.ids)]
        elif purchases:
            form_view = [(self.env.ref('purchase.purchase_order_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = purchases.id
        return action

    def action_select_loc(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Create a Transfer'),
            'res_model': 'fcb.location',
            'view_mode': 'form',
            'target': 'new',
        }
    def action_select_loc_int(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Create Intransit Transfer'),
            'res_model': 'fcb.int.location',
            'view_mode': 'form',
            'target': 'new',
        }

    def action_select_loc_to_return(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Create a Return Transfer'),
            'res_model': 'fcb.return.location',
            'view_mode': 'form',
            'target': 'new',
        }
    def action_select_loc_outsource(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Create a Outsource Transfer'),
            'res_model': 'fcb.outsource.location',
            'view_mode': 'form',
            'target': 'new',
        }

class StockPicking(models.Model):
    _inherit = 'stock.picking'
    ticket_id = fields.Many2one('helpdesk.ticket', string="Ticket Order", store=True, readonly=False, )

class HelpdeskTeam(models.Model):
    _inherit = "helpdesk.team"

    is_servicing = fields.Boolean(string="Service")


class HelpdeskTicketType(models.Model):
    _inherit = "helpdesk.ticket.type"

    ticket_type = fields.Boolean("Ticket Type")


class ServiceOrderLine(models.Model):
    _name = "service.order.line"


    product_id = fields.Many2one('product.product', string='Equipments')
    ticket_id = fields.Many2one('helpdesk.ticket',string="Services")
    product_uom_qty = fields.Float(string="Quantity")

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    ticket_id = fields.Many2one('helpdesk.ticket', string="Ticket Order", store=True, readonly=False, )
