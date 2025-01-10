# -*- coding: utf-8 -*-

import itertools
import calendar

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date
from odoo.tools.float_utils import float_round

PURCHASE_LINE_FIELDS = ['product_qty','price_unit','price_subtotal','taxes_id']

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    READONLY_STATES = {
        'purchase': [('readonly', True)],
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    }

    partner_id = fields.Many2one('res.partner', string='Vendor', required=True, states=READONLY_STATES, 
                                                change_default=True, tracking=True, 
                                                domain="['|','&', ('company_id', '=', False), ('company_id', '=', company_id), ('supplier_rank', '>', 0), ('code', 'not ilike', 'CUS')]", 
                                                help="You can find a vendor by its Name, TIN, Email or Internal Reference.")
    internal_note = fields.Text('Notes')
    supplier_code = fields.Char('Vendor Code', related="partner_id.code")
    amount_undiscounted = fields.Float('Amount Before Discount', compute='_compute_purchase_amount_undiscounted', digits=0)
    sale_id = fields.Many2one('sale.order', 'Sale')
    journal_id = fields.Many2one('account.journal', 'Billing Mode')
    user = fields.Many2one('res.users', default=lambda self: self.env.user)
    today = fields.Datetime('Date and Time', default=datetime.now())
    purchase_team_id = fields.Many2one('res.users', default=lambda self: self.env.user)
    len_note = fields.Char('Length Internal Notee', compute="_compute_purchase_internal_note", store=True)
    partner_note = fields.Text('Note (200 characters)')
    is_default_terms = fields.Boolean('Is Default Terms')
    po_comments = fields.Char(string="Comments")
    request_delivery_date = fields.Datetime("Request Delivery Date")
    estimated_delivery_date = fields.Datetime("Estimated Delivery Date")
    revision_purchase_count = fields.Float(sting="Revision Purchase Count",default=1.0)
    revision_purchase_name = fields.Char(sting="Revision Purchase Name")
    is_purchase_revise = fields.Boolean(default=False)
    artwork_attachment_ids = fields.Many2many('ir.attachment', string="ArtWork")
    mail_sended = fields.Boolean(default=False)
    state = fields.Selection([
        ('draft', 'RFQ'),
        ('sent', 'RFQ Sent'),
        ('submitted', 'Submitted for Approval'),
        ('approve', "RFQ Approved"),
        ('reject', "RFQ Rejected"),
        ('purchase', 'Purchase Order'),
        ('done', 'Locked'),
        ('cancel_approval','Cancel Approval'),
        ('cancel', 'Cancelled')
    ], string='Status', readonly=True, index=True, copy=False, default='draft', tracking=True)
    shipment_tracking_date = fields.Datetime("Date")
    cargo_clearance_permit_no = fields.Char(string="Cargo Clearance Permit No.")
    logistics = fields.Char(string="Logistics")
    total_cif = fields.Float(string='Total CIF/FOB')
    total_amount_payable = fields.Float(string='Total Amount Payable')
    api_no = fields.Char('APi No.')
    remarks_one = fields.Char('Remarks 1')
    remarks_two = fields.Char('Remarks 2')
    status = fields.Char('Status')
    next_delivery_date = fields.Datetime('Next(Earliest) Delivery Date')
    collection = fields.Selection(selection_add=[('tbc', 'TBC')], default="tbc")
    partner_request_state = fields.Selection([('none','None'),('pending','Pending'),('approved','Approved'),
                                            ('rejected','Rejected')],default='none', string='Partner Request')
    is_requested = fields.Boolean('Requested')
    approval_state = fields.Selection(
        selection=[
            ('no', 'Nothing To Approve'),
            ('approved', 'RFQ Approved'),
            ('waiting_approval', 'Waiting Approval'),
            ('reject', 'RFQ Rejected')
        ],
        string="RFQ Approval Status", default='no', readonly=True, index=True, 
        tracking=True, copy=False)
    is_contact_created = fields.Boolean(related='partner_id.is_contact_created')
    reviewed_by = fields.Many2one("res.users",string="Reviewed By")
    cancel_request_by = fields.Many2one("res.users",string="Cancel Request By")
    cancellation_reason = fields.Text(string="Cancellation Reason")
    past_state = fields.Char("Past State")
    po_req_type_id = fields.Many2one('purchase.requisition.type',related='requisition_id.type_id')
    reject_reason = fields.Text(string="Reject Reason")

    def button_cancel(self):
        for purchase in self:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Cancel Purchase Order',
                'res_model': 'purchase.order.cancellation.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_purchase_order_id': purchase.id,
                },
            }
    
    def cancellation_request_approved(self) :
        for purchase in self : 
            purchase.write({'state': 'cancel'})
            requester = purchase.cancel_request_by.partner_id
            if requester:
                purchase.message_post(
                    body=f"Your cancellation request for Purchase Order {purchase.name} has been approved.",
                    partner_ids=[requester.id]
                )
    
    def cancellation_request_rejected(self) :
        for purchase in self:
            if purchase.past_state :
                purchase.write({'state': purchase.past_state})

            # Notify requester about rejection
            requester = purchase.cancel_request_by.partner_id
            if requester:
                purchase.message_post(
                    body=f"Your cancellation request for Purchase Order {purchase.name} has been rejected.",
                    partner_ids=[requester.id]
                )


    @api.constrains('partner_note')
    def _check_partner_note_length(self):
        for record in self:
            if record.partner_note and len(record.partner_note) > 200:
                raise ValidationError("The note cannot exceed 200 characters.")

    def action_rfq_send(self):
        res = super(PurchaseOrder, self).action_rfq_send()
        active_id = self.id
        if active_id:
            po_order = self.env['purchase.order'].browse(active_id)
            if po_order:
                template_id = res.get('context', {}).get('default_template_id')
                if template_id:
                    email_template = self.env['mail.template'].browse(template_id)
                    if email_template:
                        company_name = po_order.company_id.name or ''
                        reference = po_order.name or ''
                        partner_name = po_order.partner_id.name or ''
                        modified_subject = f"{company_name} ({reference}) - {partner_name}"
                        email_template.subject = modified_subject
        return res


    def create_manager_approval(self):
        for record in self:
            record.state = "manager_approvel"

    def sc_approved(self):
        for rec in self:
            rec.state = "approved"

    def action_is_default_terms_purchase(self):
        purchase = self.env['stock.picking'].search([('is_default_terms','=',True)], limit=1)
        if purchase:
            purchase.is_default_terms = False
        else:
            for po in self:
                po.is_default_terms = True
        for po in self:
            po.is_default_terms = True

    @api.model
    def create(self, vals):
        if 'name' not in vals or vals['name'] == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('purchase.order.rfq')
        res = super(PurchaseOrder, self).create(vals)
        if self.env.context.get('create_direct_purchase'):
            res.button_confirm()
        default_terms = self.env['purchase.order'].search([('is_default_terms', '=', True)], limit=1).notes
        if default_terms:
            vals['notes'] = default_terms
        if res.partner_id.code:
            res.write({'partner_request_state': 'approved'})
        return res
    
    def write(self,vals):
        for purchase in self:
            if vals.get('order_line'):
                order_line_vals = list(map(lambda y:list(y[-1].keys()),filter(lambda x:isinstance(x,list) and isinstance(x[-1],dict),vals.get('order_line'))))
                if any(field in PURCHASE_LINE_FIELDS for field in list(itertools.chain(*order_line_vals))):
                    vals['revision_purchase_name'] = (purchase.name.split('-')[0] if not purchase.revision_purchase_name else purchase.revision_purchase_name.split('-')[0]) + '-R%s'%(int(purchase.revision_purchase_count + 1) if int(purchase.revision_purchase_count) == 0 else int(purchase.revision_purchase_count))
                    original_name = self.name.split('-R')
                    main_po = self.search([('name', '=', original_name[0]), ('id', '!=', self.id)])
                    if main_po:
                        vals['name'] = (main_po.name.split('-')[0] if not main_po.revision_purchase_name else main_po.revision_purchase_name.split('-')[0]) + '-R%s'%(int(main_po.revision_purchase_count + 1) if int(main_po.revision_purchase_count) == 0 else int(main_po.revision_purchase_count))
                        main_po.revision_purchase_count = main_po.revision_purchase_count + 1
                        vals['revision_purchase_count'] = main_po.revision_purchase_count + 1
                    else:
                        vals['revision_purchase_count'] = purchase.revision_purchase_count + 1
                        vals['name'] = (purchase.name.split('-')[0] if not purchase.revision_purchase_name else purchase.revision_purchase_name.split('-')[0]) + '-R%s'%(int(purchase.revision_purchase_count + 1) if int(purchase.revision_purchase_count) == 0 else int(purchase.revision_purchase_count))
                    vals['is_purchase_revise'] = True
        return super(PurchaseOrder,self).write(vals)

    # add function change estimated  date based on po to poline
    @api.onchange('estimated_delivery_date','request_delivery_date')
    def _compute_purchase_estimated_delivery_date(self):
        for rec in self:
            if rec.estimated_delivery_date or rec.request_delivery_date:
                self.order_line.write({'estimated_delivery_date': self.estimated_delivery_date,
                                       'request_delivery_date': self.request_delivery_date})
            else:
                self.order_line.write({'estimated_delivery_date': self.estimated_delivery_date,
                                       'request_delivery_date': self.request_delivery_date})

    def _compute_purchase_internal_note(self):
        self.len_note = False
        for inv in self:
            if inv.partner_note:
                inv.len_note = len(inv.partner_note)
            else:
                inv.len_note = False

    def _compute_purchase_amount_undiscounted(self):
        for order in self:
            total = 0.0
            for line in order.order_line:
                total += line.price_subtotal + line.price_unit * ((line.discount or 0.0) / 100.0) * line.product_uom_qty  # why is there a discount in a field named amount_undiscounted ??
            order.amount_undiscounted = total

    def _prepare_invoice(self):
        """Prepare the dict of values to create the new invoice for a purchase order.
        """
        self.ensure_one()
        move_type = self._context.get('default_move_type', 'in_invoice')

        partner_invoice = self.env['res.partner'].browse(self.partner_id.address_get(['invoice'])['invoice'])
        partner_bank_id = self.partner_id.commercial_partner_id.bank_ids.filtered_domain(['|', ('company_id', '=', False), ('company_id', '=', self.company_id.id)])[:1]


        invoice_vals = {
            'ref': self.partner_ref or '',
            'move_type': move_type,
            'narration': self.notes,
            'currency_id': self.currency_id.id,
            'invoice_user_id': self.user_id and self.user_id.id or self.env.user.id,
            'partner_id': partner_invoice.id,
            'fiscal_position_id': (self.fiscal_position_id or self.fiscal_position_id._get_fiscal_position(partner_invoice)).id,
            'payment_reference': self.partner_ref or '',
            'partner_bank_id': partner_bank_id.id,
            'invoice_origin': self.name,
            'invoice_payment_term_id': self.payment_term_id.id,
            'invoice_line_ids': [],
            'company_id': self.company_id.id,
            'purchase_order_id': self.id
        }
        return invoice_vals


    @api.onchange('partner_id')
    def onchange_partner_to_get_purchasenote(self):
        for order in self:
            if order.partner_id:
                config_note = self.env['fischerbell.configuration.note'].search([
                    ('type', '=', 'purchase'),
                    ('partner_ids', 'in', [order.partner_id.id])  # Use a list to compare with a Many2many field
                ], limit=1)
                order.partner_note = config_note.note


    # def button_confirm(self):
    #   # if self.request_delivery_date and self.estimated_delivery_date and self.mail_sended:
    #   if self.mail_sended:
    #       res = super().button_confirm()
    #       for order in self:
    #           if order.state == 'purchase':
    #               order.write({'name': self.env['ir.sequence'].next_by_code('purchase.order.po')})
    #               if order.picking_ids:
    #                   for pick in order.picking_ids:
    #                       pick.user = self.env.user.id
    #       return res
    #   else:
    #       if not self.mail_sended:
    #           raise ValidationError("Please Send Email First")

    def button_confirm_wizard(self):
    # if self.request_delivery_date and self.estimated_delivery_date and self.mail_sended:
        if self.mail_sended:
            self.ensure_one()
            return {
                'type': 'ir.actions.act_window',
                'name': 'Invoice Policy',
                'view_mode': 'form',
                'res_model': 'invoice.policy.wizard',
                'domain': [],
                'context': {'is_purchase':True},
                'target': 'new',
            }
        else:
            if not self.mail_sended:
                raise ValidationError("Please Send Email First")


    def _prepare_picking(self):
        res = super(PurchaseOrder, self)._prepare_picking()
        res.update({
            "artwork_attachment_ids": [(6, 0, self.artwork_attachment_ids.ids)]
        })
        return res

    def check_planned_date(self, order_date_planned):
        if order_date_planned:
            partner_ids = self.partner_id
            for partner_id in partner_ids:
                if partner_id.no_delivery_days_selection == 'days':
                    if eval(partner_id.no_delivery_days) == order_date_planned.weekday():
                        raise UserError('The customer %s is not available at this day %s, please change it as per the customers availability' % (partner_id.name,calendar.day_name[eval(partner_id.no_delivery_days)]))
                elif partner_id.no_delivery_days_selection == 'date':
                    if partner_id.delivery_restriction_start_date <= order_date_planned.date() <= partner_id.delivery_restriction_end_date:
                        raise UserError('The customer %s is not available at this date %s, please change it as per the customers availability' % (partner_id.name,order_date_planned))


    @api.depends('order_line.date_planned')
    def _compute_date_planned(self):
        """ date_planned = the earliest date_planned across all order lines. """
        for order in self:
            dates_list = order.order_line.filtered(lambda x: not x.display_type and x.date_planned).mapped('date_planned')
            if dates_list:
                order.date_planned = min(dates_list)
            else:
                order.date_planned = False
            self.check_planned_date(order.date_planned)
    
    def create_sequance_contact(self):
        for purchase in self:
            purchase.write({'partner_request_state':'pending',
                        'is_requested':True})

    def request_approved(self):
        for purchase in self:
            if not purchase.partner_id.code:
                code = self.env['ir.sequence'].next_by_code('res.partner.vendor') or _('New')

                purchase.partner_id.write({
                    'code': code,
                    'supplier_rank': purchase.partner_id.supplier_rank,
                    'is_contact_created': True,
                    'property_product_pricelist': purchase.partner_id.property_product_pricelist.id if purchase.partner_id.property_product_pricelist else False
                })

            purchase.write({
                'partner_request_state': 'approved',
                'partner_id': purchase.partner_id.id
            })

    def request_rejected(self):
        for purchase in self:
            purchase.write({'partner_request_state':'rejected'})


    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        landed_cost_product = self.env['product.product'].search([('landed_cost_ok', '=', True)], limit=1)
        if self.partner_id.currency_type == 'overseas':
            if not landed_cost_product:
                raise UserError("Please create a freight charge product.")
            else:
                self.order_line = [(0, 0, {
                    'product_id': landed_cost_product.id,
                    'product_qty': 1.0,
                    'price_unit': landed_cost_product.standard_price,
                    'name': landed_cost_product.name,
                    'date_planned': fields.Date.today(),
                    'product_uom': landed_cost_product.uom_id.id,
                })]
        else:
            # Remove the landed cost product from the order lines if it's there
            self.order_line = [(5, 0, 0)] + [
                (1, line.id, {}) for line in self.order_line
                if line.product_id != landed_cost_product
            ]

    @api.model
    def _get_picking_type(self, company_id):
        if self.env.user.company_id and self.env.user.company_id.warehouse_id:
            picking_type = self.env['stock.picking.type'].search([('code', '=', 'incoming'), 
                                                                    ('warehouse_id.company_id', '=', self.env.user.company_id.id),
                                                                    ('warehouse_id','=',self.env.user.company_id.warehouse_id.id)])
            return picking_type[:1]
        picking_type = self.env['stock.picking.type'].search([('code', '=', 'incoming'), ('warehouse_id.company_id', '=', company_id)])
        if not picking_type:
            picking_type = self.env['stock.picking.type'].search([('code', '=', 'incoming'), ('warehouse_id', '=', False)])
        return picking_type[:1]

    def _prepare_picking(self):
        res = super(PurchaseOrder, self)._prepare_picking()
        location_id = res['location_dest_id'] 
        if self.env.user.company_id and self.env.user.company_id.warehouse_id:
            location_id = self.picking_type_id.default_location_dest_id.id
        res['location_dest_id'] = location_id
        return res

    def button_confirm(self):
        for order in self:
            product_ids = order.order_line.filtered(lambda x:x.product_id.approval_request in ('draft','rejected'))
            if product_ids:
                raise ValidationError(_('Product must be Approved for the Order Confirmation. \nThis Products is not Approved: %s')%(',\n '.join(product_ids.mapped('product_id').mapped('name'))))
            if order.state not in ['draft', 'approve']:
                continue
            order.order_line._validate_analytic_distribution()
            order._add_supplier_to_product()
            order.button_approve()
            if order.partner_id not in order.message_partner_ids:
                order.message_subscribe([order.partner_id.id])
        return True

    def action_to_approve(self):
        for order in self:
            if order.state == 'submitted' and order.approval_state == 'waiting_approval' and self.env.user.has_group("fischerbell_custom.group_purchase_order_approver"):
                order.write({
                    'state': 'approve',
                    'approval_state': 'approved',
                    'reviewed_by': self.env.user.id
                })
            else:
                raise ValidationError("Sorry, you are not allowed to reject this order.")

    def action_to_reject(self):
        for order in self:
            if order.state == 'submitted' and order.approval_state == 'waiting_approval' and self.env.user.has_group("fischerbell_custom.group_purchase_order_approver"):
                return {'name': 'Reject Reason',
                    'type': 'ir.actions.act_window',
                    'res_model': 'reject.reason.wizard',
                    'view_mode': 'form',
                    'view_type': 'form',
                    'target': 'new',
                    'context': {'default_reason': '', 'active_id': self.id, 'purchase_id': self.id, 'is_purchase': True},}
            else:
                raise ValidationError("Sorry, you are not allowed to reject this order.")
    
    def action_submit_approval(self):
        for rec in self:
            item_zero = []
            for line in self.order_line.filtered(lambda x:x.display_type not in ['line_section', 'line_note']):
                if line.price_subtotal == 0:
                    item_zero.append("- " + line.product_id.name if line.product_id else '')
            if item_zero:
                message = "Purchase Order Line found with 0 Subtotal: \n{}".format("\n".join(item_zero))
                raise UserError(message)
            user_id = self.env['res.users'].sudo().search([('groups_id', 'in', self.env.ref('fischerbell_custom.group_purchase_order_approver').id)], limit = 1)
            if not user_id:
                user_id = self.env['res.users'].sudo().search([('groups_id', 'in', self.env.ref('account.group_account_manager').id)], limit = 1)
            self.env['mail.activity'].sudo().create({
                'res_model_id': self.env.ref('purchase.model_purchase_order').id,
                'res_id': rec.id,
                'user_id': user_id.id,
                'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                'summary': _('Approval of RFQ : %s'%rec.name),
                'note': _('<span>Hello, <b>%s</b>, just a quick reminder to review and approve the pending RFQ <b>%s</b>.</br> Thanks!')%(user_id.name, rec.name)
            })
            rec.write({'state': 'submitted', 'approval_state': 'waiting_approval'})

    def copy(self, default=None):
        if self.state == 'purchase':
            default = dict(default or {})
            original_name = self.name.split('-R')
            main_po = self.search([('name', '=', original_name[0])])
            if main_po:
                main_po = main_po
            else:
                main_po = self
            default['name'] = (main_po.name.split('-')[0] if not main_po.revision_purchase_name else main_po.revision_purchase_name.split('-')[0]) + '-R%s'%(int(main_po.revision_purchase_count + 1) if int(main_po.revision_purchase_count) == 0 else int(main_po.revision_purchase_count))
            main_po.revision_purchase_count = main_po.revision_purchase_count + 1
            default['revision_purchase_count'] = main_po.revision_purchase_count
            new_po = super(PurchaseOrder, self).copy(default=default)
            new_po.button_confirm()
            return new_po
        else:
            return super(PurchaseOrder, self).copy(default=default)


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    def get_last_purchase_order(self):
        order_id = False
        if self.product_id and self.order_id and self.order_id.partner_id:
            partner_id = self.sudo().order_id.partner_id.id
            product_id = self.sudo().product_id and self.product_id.id
            order_line_ids = self.env['purchase.order.line'].search([('product_id', '=', product_id)])
            order_list_ids = [line.order_id.id for line in order_line_ids]
            domain = [('id', 'in', list(set(order_list_ids))), ('state', '=', 'purchase')]
            # If same Vendor
            # domain = [('id', 'in', list(set(order_list_ids))), ('state', '=', 'purchase'),
            #           ('partner_id', '=', partner_id)]
            if self.order_id and self.order_id.id:
                domain.append(('id', '!=', self.order_id.id))
            order_ids = self.env['purchase.order'].search(domain, order='id')
            order_id = False
            if order_ids:
                order_id = [order for order in order_ids][-1]
        return order_id

    @api.depends('order_id', 'order_id.partner_id', 'product_id')
    def get_purchase_order_last_purchase_price(self):
        for obj in self:
            order_id = obj.sudo().get_last_purchase_order()
            product_price = 0.0
            if obj.product_id:
                if order_id:
                    product_price = 0.0
                    for line in order_id.order_line:
                        if line.product_id.id == obj.product_id.id:
                            product_price = obj.price_unit
            obj.sudo().last_purchase_price = product_price
            obj.sudo().last_po_id = order_id

    def action_open_last_purchase_order(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Purchase Order',
            'view_mode': 'form',
            'res_model': 'purchase.order',
            'res_id': self.sudo().last_po_id.id,
            'target': 'current',  # or 'new' to open in a new window
        }

    customer_id = fields.Many2one('res.partner', 'Customer Name')
    batch_number = fields.Char('Batch Number', related="customer_id.batch_number")
    lot_id = fields.Many2one('stock.lot', 'Serial Number')
    product_tmpl_id = fields.Many2one('product.template')
    discount = fields.Float(string='Discount (%)', digits='Discount', default=0.0)
    product_template_id = fields.Many2one('product.template', 'Product Template', related="product_id.product_tmpl_id")
    customer_sku = fields.Char('Customer SKU')
    sale_id = fields.Many2one('sale.order', related="sale_line_id.order_id")
    manufacture_lot_id = fields.Many2one('fischerbell.manufacture.lot', 'Manufacture No')
    comments = fields.Char()
    request_delivery_date = fields.Datetime("Request Delivery Date")
    estimated_delivery_date = fields.Datetime("Estimated Delivery Date")
    approval_state = fields.Selection([('draft', 'Draft'), ('approved', 'Approved'), ('rejected', 'rejected')], string='State', default='draft')
    po_reason = fields.Text(string="Reason")
    last_purchase_price = fields.Float("Last Purchase Price", compute="get_purchase_order_last_purchase_price")
    last_po_id = fields.Many2one("purchase.order", "Last Purchase Order")


    def action_approve_line(self):
        for line in self:
            line.approval_state = 'approved'

    def action_reject_line(self):
        for line in self:
            return {'name': 'Reject Reason',
                    'type': 'ir.actions.act_window',
                    'res_model': 'reject.reason.wizard',
                    'view_mode': 'form',
                    'view_type': 'form',
                    'target': 'new',
                    'context': {'default_reason': '', 'active_id': self.id},}

    @api.onchange('product_id')
    def onchange_sake_product_image(self):
        for product in self:
            if product.order_id.estimated_delivery_date:
                product.estimated_delivery_date = product.order_id.estimated_delivery_date
                product.request_delivery_date = product.order_id.request_delivery_date
            else:
                product.estimated_delivery_date = False
                product.request_delivery_date = False


    @api.onchange('customer_id')
    def onchange_purchase_customer_sku(self):
        if self.customer_id and self.product_id.product_tmpl_id and self.product_id.product_tmpl_id.use_customer_sku:
            customer_sku = ''
            for line in self.product_id.product_tmpl_id.customer_sku_ids:
                if line.customer_id == self.customer_id and line.customer_sku:
                    customer_sku = line.customer_sku
            if customer_sku:
                self.customer_sku = customer_sku
            else:
                self.customer_sku = ''
        else:
            self.customer_sku = ''

    def _get_product_purchase_description(self, product_lang):
        self.ensure_one()
        size = ''
        for product in product_lang.product_variant_ids:
            if product_lang == product:
                for line in product.product_template_variant_value_ids:
                    size += line.display_name
        name = product_lang.name
        if product_lang.description_purchase and size:
            name += ' ' + size + '\n' + product_lang.description_purchase
        elif product_lang.description_purchase:
            name += '\n' + product_lang.description_purchase
        elif size:
            name += ' ' + size
        else:
            pass
        return name


    def _prepare_account_move_line(self, move=False):
        res = super()._prepare_account_move_line()
        sale_ids = False
        picking_ids = False
        move_ids = False
        context = self._context
        list_so = []
        invoice_vals = False
        for line in self:
            if context.get('create_bill') == True:
                list_so.append(line.sale_line_id.order_id.id)
                if list_so:
                    sale_ids = self.env['sale.order'].search([('id', 'in', list_so)])
                    picking_ids = self.env['stock.picking'].search([('sale_id', 'in', sale_ids.ids),('picking_type_code','=','outgoing'),('state','!=','cancel')])
                    move_ids = self.env['account.move'].search([('move_type','=','out_invoice'),('sale_id','in',sale_ids.ids)])

        res.update({'sale_ids': sale_ids,'move_ids': move_ids, 'picking_ids': picking_ids})
        return res

    def _create_stock_moves(self, picking):
        return super(PurchaseOrderLine, self.filtered(lambda x: x.approval_state != 'rejected'))._create_stock_moves(picking)