# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from itertools import groupby

from odoo import api,fields, models, _
from odoo.exceptions import UserError, ValidationError, AccessError
from datetime import datetime, timedelta, date
from odoo.fields import Command
import re
import itertools
import pytz
from collections import defaultdict  # Add this import

READONLY_FIELD_STATES = {
    state: [('readonly', True)]
    for state in {'sale', 'done', 'cancel'}
}

ORDER_LINE_FIELDS = ['product_uom_qty','price_unit','price_subtotal','tax_id']


class ProductVendorConf(models.Model):
    _name = "product.vendor.conf"
    _description = "Product Vendor Conf"

    product_id = fields.Many2one('product.product',string="Product")
    partner_id = fields.Many2one('res.partner',string="Vendor")
    sale_id = fields.Many2one('sale.order',string="Order")
    sale_line_id = fields.Many2one('sale.order.line',string="Sale Order Line")
    supplier_info_id = fields.Many2one('product.supplierinfo')
    bom_line_id = fields.Many2one('mrp.bom.line')


class SaleOrder(models.Model):
    _inherit = "sale.order"

    # attn_to = fields.Char('Attn To', related="partner_id.attn_to")
    origin = fields.Char(
        string="Source Document(PO REF)",
        help="Reference of the document that generated this sales order request")
    type = fields.Selection([
        ('sale', 'Sale Order'),
        ('loan', 'Loan Order'),
        ('exchange', 'Exchange Order'),
        ('training', 'Training'),
        ('replacement', 'Replacement Order')
    ], default='sale')
    loan_state = fields.Selection([
        ('open', 'Open'),
        ('closed', 'Closed'),
        ('not_loan', 'Not Loan')
    ], compute="_compute_loan_state", store=True)
    loan_date = fields.Date('Loan Date', compute="_compute_loan_state", store=True)
    billing_state = fields.Selection([
        ('open', 'Open'),
        ('closed', 'Closed'),
        ('no_invoice','No Invoice')
    ], compute="_compute_billing_state")
    sale_id = fields.Many2one('sale.order', 'Sale')
    # exchange_order_ids = fields.One2many('sale.order', 'sale_id', string="Exchange Order")
    # exchange_order_count = fields.Integer('Exchange Order Count', compute="_compute_exchange_order_ids")
    loan_ids = fields.One2many('sale.order','sale_id',string="Loan Order")
    loan_order_count = fields.Integer('Loan Order Count', compute="_compute_loan_ids")
    # replacement_order_ids = fields.One2many('sale.order', 'sale_id', string="Replacement Order")
    # replacement_order_count = fields.Integer('Replacement Order Count', compute="_compute_replacement_order_ids")
    partner_invoice_address = fields.Char()
    check_partner_address = fields.Boolean('Check Partner Address', default=False)
    customer_code = fields.Char('Customer Code', related="partner_id.code")
    terms_and_conditions = fields.Html('Terms and Conditions', compute="_get_terms_and_conditions")
    purchase_ref = fields.Char('Purchase Reference', compute="_compute_purchase_ref", store=True)
    journal_id = fields.Many2one('account.journal', 'Billing Mode')
    user = fields.Many2one('res.users', default=lambda self: self.env.user)
    today = fields.Datetime(string='Singapore Date & Time', default=datetime.now(), tz='Asia/Indonesia')
    len_note = fields.Char('Length Internal Notee', compute="_compute_sale_internal_note", store=True)
    partner_note = fields.Text('Note')
    delivery_type = fields.Selection([
        ('self_collection', 'Self Collection'),
        ('in_house_driver', 'Delivery by In-house Driver'),
        ('third_party_logistics','Delivery by Third-party Logistics')
    ], default='self_collection')
    route_id = fields.Many2one('fischerbell.delivery.route', 'Delivery Route')
    approval_state = fields.Selection(
        selection=[
            ('no', 'Nothing To Approve'),
            ('approved', 'Quotation Approved'),
            ('waiting_approval', 'Waiting Approval'),
            ('reject', 'Quotation Rejected')
        ],
        string="Quotation Approval Status", default='no', tracking=True)
    is_approved = fields.Boolean('Is Approved')
    state = fields.Selection(
        selection=[
            ('draft', "Quotation"),
            ('sent', "Quotation Sent"),
            # ('waiting_approval', 'Waiting Approval'),
            ('approve', "Quotation Approved"),
            ('reject', "Quotation Rejected"),
            ('sale', "Sales Order"),
            ('done', "Locked"),
            ('cancel', "Cancelled"),
        ],
        string="Status",
        readonly=True, copy=True, index=True,
        tracking=3,
        default='draft')

    contact_person_id = fields.Many2one('res.partner', string='Contact Person')
    contact_person_comp_id = fields.Many2one('res.partner', string='Contact Person Company',compute="_get_contact_person_company")
    # contact_person_comp_id = fields.Many2one('res.partner', string='Contact Person Company',related="contact_person_id.parent_id")
    contact_per_name = fields.Char(string="Contact Person Name",readonly=True)
    revision_order_count = fields.Float(sting="Revision Order Count",default=1.0)
    revision_order_name = fields.Char(sting="Revision Order Name")
    is_order_revise = fields.Boolean(default=False)
    reviewed_by = fields.Many2one("res.users",string="Reviewed By")
    email_to_customer = fields.Datetime(string="Email To Customer")
    first_followup_date = fields.Datetime(string="First Follow Up")
    sec_followup_date = fields.Datetime(string="Sec Follow Up")
    scheduled_delivery_date = fields.Datetime(string="Scheduled Delivery Date")
    requested_delivery_date = fields.Datetime(string="Requested Delivery Date")
    no_enough_stock = fields.Boolean(compute='_compute_order_stock')
    over_credit_limit = fields.Boolean(compute='_compute_credit_limit', store=True)
    send_mail_credit_limit = fields.Boolean(string='Send Mail Credit Limit')
    submited_date = fields.Date('Submited Date')
    artwork_attachment_ids = fields.Many2many('ir.attachment',string="ArtWork")
    delivery_instruction = fields.Html(string="Delivery Instruction")
    invoice_instruction = fields.Html(string="Invoice Instruction")
    delivery_option = fields.Selection(
        selection=[('partial_delivery', 'Partial Delivery'),
            ('full_delivery', 'Wait for the receival of all goods')],
        string="Delivery Option", default='partial_delivery')
    collection = fields.Selection(selection_add=[('tbc', 'TBC')], default="tbc")
    product_vendor_conf_ids = fields.One2many('product.vendor.conf','sale_id',string="Product Vendor Conf")
    partner_request_state = fields.Selection([('none','None'),('pending','Pending'),('approved','Approved'),
                                            ('rejected','Rejected')],default='none', string='Partner Request')
    is_requested = fields.Boolean('Requested')
    is_contact_created = fields.Boolean(related='partner_id.is_contact_created')
    order_id = fields.Many2one('sale.order', compute="_get_order_id")
    is_rx_eywear = fields.Boolean(string = 'Is RX - Eywear')
    sub_order_ids = fields.Many2many('sale.order','rel_sale_order_sale','sale_id','sub_order_id', string="Sub Order")
    sub_order_count = fields.Integer('Sub Order Count', compute='action_view_saleorder')
    is_approved_sale = fields.Boolean()
    sale_reason = fields.Text()
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string="Customer",
        required=True, readonly=False, change_default=True, index=True,
        tracking=1,
        states=READONLY_FIELD_STATES,
        domain="['|', ('code', '=', False), ('code', 'ilike', 'CUS')]")
    hide_send_by_email = fields.Boolean('Hide Send By Email', compute="_compute_hide_send_by_email")
    count_ticket = fields.Integer(compute="_compute_count_ticket")
    count_services = fields.Integer(compute="_compute_count_services")

    def _compute_count_services(self):
        for rec in self:
            for record in self:
                ticket_id = self.env['helpdesk.ticket'].search([('sale_id', '=', record.id)])
                rec.count_services = len(ticket_id.fsm_task_ids)

    def action_view_task(self):
        self.ensure_one()
        ticket_id = self.env['helpdesk.ticket'].search([('sale_id', '=', self.id)])
        return {
            'type': 'ir.actions.act_window',
            'name': 'Services',
            'view_mode': 'tree,form',
            'res_model': 'project.task',
            'domain': [('id', 'in', ticket_id.fsm_task_ids.ids)],
            'context': {'create': False, 'edit': False},
            'target': 'current'
        }

    def _compute_count_ticket(self):
        for rec in self:
            for record in self:
                ticket_id = self.env['helpdesk.ticket'].search([('sale_id', '=', record.id)])
                rec.count_ticket = len(ticket_id)

    def action_view_ticket(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Ticket',
            'view_mode': 'tree,form',
            'res_model': 'helpdesk.ticket',
            'domain': [('sale_id', '=', self.id)],
            'context': {'create': False, 'edit': False},
            'target': 'current'
        }

    def create_ticket(self):
        """Open the Service Helpdesk Ticket wizard as a popup."""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Helpdesk Ticket',
            'res_model': 'service.helpdesk.ticket',
            'view_mode': 'form',
            'view_id': self.env.ref('fischerbell_custom.view_service_helpdesk_ticket_wizard_form').id,
            'target': 'new',
            'context': {
                'default_partner_id': self.partner_id.id,
                'default_sale_id': self.id,

            },
        }

    followup_reminder_sent = fields.Boolean(string="Follow-up Reminder Sent", default=False)

    def _send_followup_reminders(self):
        """
        Send follow-up reminders for quotations sent 3 days ago.
        """
        today = fields.Date.today()
        three_days_ago = today - timedelta(days=3)
        quotations = self.sudo().search([
            ('state', '=', 'sent'),  # Quotation state
            ('followup_reminder_sent', '=', False),  # Not already sent
            ('date_order', '>=', three_days_ago)  # Sent 3 days ago
        ])
        for quotation in quotations:
            template = self.env.ref('fischerbell_custom.followup_quotation_email_template')
            if template:
                template.send_mail(quotation.id, force_send=True)
                quotation.followup_reminder_sent = True

    def _get_order_id(self):
        for rec in self:
            rec.order_id = False
            if rec.name:
                rec.order_id = self.search([('name', '=', rec.name)], limit=1).id

    @api.depends('partner_id')
    def _compute_partner_shipping_id(self):
        for order in self:
            order.partner_shipping_id = order.partner_id.address_get(['delivery'])['delivery'] if order.partner_id else False
            order.route_id = order.get_route_id(order.partner_shipping_id)


    def get_route_id(self, partner_shipping_id):
        if partner_shipping_id and partner_shipping_id.zip:
            postal_code = '{:.2}'.format(partner_shipping_id.zip)
            zip_number = self.env['fischerbell.delivery.route.line'].search([('name','=',postal_code)], limit=1)
            return zip_number.route_id.id if zip_number else False
        else:
            return False

    def _compute_order_stock(self):
        for order in self:
            order.no_enough_stock = True
            no_stock = any(line.product_uom_qty > line.product_template_id.qty_available for line in order.order_line)
            if no_stock:
                order.no_enough_stock = False

    @api.depends('partner_id', 'amount_total')
    def _compute_credit_limit(self):
        for order in self:
            order.over_credit_limit = False
            if order.amount_total > order.partner_id.credit_limit and order.partner_id.credit_limit != 0:
                order.over_credit_limit = True


    @api.onchange('scheduled_delivery_date')
    def _onchange_partner_not_avalibale(self):
        partner = self.partner_id.parent_id if self.partner_id.parent_id else self.partner_id
        if partner.no_delivery_days_selection == 'days' and int(partner.no_delivery_days) == self.scheduled_delivery_date.weekday():
            raise ValidationError("Customer is not available during this date")
        if partner.no_delivery_days_selection == 'date' and partner.delivery_restriction_start_date <= self.scheduled_delivery_date.date() <= partner.delivery_restriction_end_date:
            raise ValidationError(f"Customer is not available from {partner.delivery_restriction_start_date.strftime('%d-%m-%Y')} to {partner.delivery_restriction_end_date.strftime('%d-%m-%Y')}")
        
    def _get_contact_person_company(self):
        for rec in self:
            if rec.contact_person_id:
                rec.contact_person_comp_id = rec.contact_person_id.parent_id.id
                rec.contact_per_name = rec.contact_person_id.name
            else:
                rec.contact_person_comp_id = False

    def _update_approval_state(self):
        orders = self.env['sale.order'].search([('approval_state','=','no')])
        for order in orders:
            if order.state == 'draft':
                order.approval_state = 'no'
            if order.state == 'sale' and order.picking_ids:
                order.approval_state = 'approved'
            if order.state == 'cancel':
                order.approval_state = 'reject'


    def action_to_approve(self):
        self.submited_date = date.today()
        self.approval_order()
        for record in self:
            location_ids = []
            # Find lines where the product's available quantity is less than or equal to 0
            lines_not_invoiced = record.order_line.filtered(lambda line: line.product_id.qty_available <= 0.0)
            # Group lines by their location (using a dictionary)
            lines_by_location = defaultdict(list)
            for lines in lines_not_invoiced:
                quant_ids = self.env['stock.quant'].search(
                    [('product_id', '=', lines.product_id.id), ('reserved_quantity', '=', 0.0)], limit=1)
                if quant_ids:
                    location = quant_ids.location_id
                    location_ids.append(location.name)
                    # Group lines by location
                    lines_by_location[location].append(lines)

            # Iterate through the grouped lines by location and create pickings
            for location, lines_group in lines_by_location.items():
                picking_type = self.env['stock.picking.type'].search([('code', '=', 'internal')], limit=1)
                picking = self.env['stock.picking'].create({
                    'picking_type_id': picking_type.id,
                    'partner_id': record.partner_id.id,
                    'origin': record.name,
                    'sale_id': record.id,
                    'location_id': location.id,
                    'location_dest_id': record.warehouse_id.lot_stock_id.id,
                    'move_ids_without_package': [(0, 0, {
                        'name': line.product_id.name,
                        'product_id': line.product_id.id,
                        'product_uom_qty': line.product_uom_qty,
                        'product_uom': line.product_uom.id,
                        'location_id': location.id,
                        'location_dest_id': record.warehouse_id.lot_stock_id.id
                    }) for line in lines_group]  # Grouped lines per location
                })
                # Confirm and validate the picking
                picking.action_confirm()
        return True

    def approval_order(self):
        for order in self:
            # if order.partner_id.credit_limit > 0:
            if order.amount_total < order.partner_id.credit_limit:
                if order.state == 'waiting_approval' and order.approval_state == 'waiting_approval' and self.env.user.has_group(
                        "fischerbell_custom.group_sales_order_approver"):
                    order.write({
                        'state': 'approve',
                        'approval_state': 'approved',
                        'reviewed_by': self.env.user.id
                    })
                    order.with_context(vendor_wizard=True).action_confirm()

                    purchase_order_ids = self._get_purchase_orders()
                    if purchase_order_ids:
                        purchase_id = purchase_order_ids[0]
                        return {
                            'name': "Low Stock Alert",
                            'type': 'ir.actions.act_window',
                            'view_type': 'form',
                            'view_mode': 'form',
                            'res_model': 'purchase.order.ref',
                            'context': {
                                'default_name': f"Sale order - {order.name} has some products which are having low stock, please find the details below:\n{','.join(purchase_id.order_line.mapped('product_id.name'))}\nPurchase Order Ref: {purchase_id.name}"
                            },
                            'view_id': self.env.ref('fischerbell_custom.purchase_order_ref_form_view').id,
                            'target': 'new'
                        }
                    not_enough_stock = any(
                        line.product_uom_qty > line.product_id.qty_available for line in order.order_line)
                    if order.partner_id.credit_limit > 0:
                        return {'warning': {
                            'title': _("Warning"),
                            'message': "Customer exceeded the credit limit"
                        }}
                    if not_enough_stock:
                        pass
                else:
                    raise ValidationError("Sorry, you are not allowed to approve this order.")
                # else:
                #   raise ValidationError("Customer exceeded the credit limit.")
            else:
                if order.state == 'waiting_approval' and order.approval_state == 'waiting_approval' and self.env.user.has_group(
                        "fischerbell_custom.group_sales_order_approver"):
                    order.write({
                        'state': 'approve',
                        'approval_state': 'approved',
                        'reviewed_by': self.env.user.id
                    })
          
     # if order.partner_id.partner_seq == _('New'):
     #  partner = self.env['res.partner'].browse(order.partner_id.id)
     #  partner.update({
     #      'partner_seq': self.env['ir.sequence'].next_by_code('res.partner') or _('New')
     #  })
                    order.with_context(vendor_wizard=True).action_confirm()

                    purchase_order_ids = self._get_purchase_orders()
                    if purchase_order_ids:
                        purchase_id = purchase_order_ids[0]
                        return {
                            'name': "Low Stock Alert",
                            'type': 'ir.actions.act_window',
                            'view_type': 'form',
                            'view_mode': 'form',
                            'res_model': 'purchase.order.ref',
                            'context': {
                                'default_name': f"Sale order - {order.name} has some products which are having low stock, please find the details below:\n{','.join(purchase_id.order_line.mapped('product_id.name'))}\nPurchase Order Ref: {purchase_id.name}"
                            },
                            'view_id': self.env.ref('fischerbell_custom.purchase_order_ref_form_view').id,
                            'target': 'new'
                        }
                    not_enough_stock = any(
                        line.product_uom_qty > line.product_id.qty_available for line in order.order_line)
                    if order.partner_id.credit_limit > 0:
                        return {'warning': {
                            'title': _("Warning"),
                            'message': "Customer exceeded the credit limit"
                        }}
                    if not_enough_stock:
                        pass
                else:
                    raise ValidationError("Sorry, you are not allowed to approve this order.")

    def action_stock_confirm(self):
        self.ensure_one()
        outgoing_delivery_ids = self.picking_ids.filtered(lambda delivery: delivery.picking_type_code == 'outgoing')
        for delivery in outgoing_delivery_ids:
            delivery.enough_stock = False

    def action_to_reject(self):
        for order in self:
            if order.state == 'sent' and order.approval_state == 'waiting_approval' and self.env.user.has_group("fischerbell_custom.group_sales_order_approver"):
                order.write({
                    'state': 'reject',
                    'approval_state': 'reject',
                    'reviewed_by': self.env.user.id
                })
            else:
                raise ValidationError("Sorry, you are not allowed to reject this order.")

        return True

    def action_approve(self):
        for order in self:
            if order.state == 'sent' and order.approval_state == 'waiting_approval' and self.env.user.has_group("fischerbell_custom.group_sales_order_approver"):
                request_state = 'none'
                if order.partner_id.code:
                    request_state = 'approved'
                order.write({
                    'state': 'approve',
                    'partner_request_state':request_state,
                    'approval_state': 'approved',
                    'reviewed_by': self.env.user.id
                })
                if order.have_special_permission : 
                    order.write({
                        'invoice_status': 'to invoice',
                    })
            else:
                raise ValidationError("Sorry, you are not allowed to reject this order.")
        return True

    @api.depends('partner_note')
    def _compute_sale_internal_note(self):
        self.len_note = False
        for inv in self:
            if inv.partner_note:
                inv.len_note = len(inv.partner_note)
            else:
                inv.len_note = False

    @api.depends('order_line.price_unit')
    def _compute_hide_send_by_email(self):
        self.hide_send_by_email = False
        for order in self:
            if any(order.order_line.filtered(lambda line: line.price_unit < line.product_template_id.list_price)):
                self.hide_send_by_email = True
            else:
                self.hide_send_by_email = False

    def action_submit_to_approval(self):
        for order in self:
            user_id = self.env['res.users'].sudo().search([('groups_id', 'in', self.env.ref('fischerbell_custom.group_purchase_order_approver').id)], limit = 1)
            if not user_id:
                user_id = self.env['res.users'].sudo().search([('groups_id', 'in', self.env.ref('account.group_account_manager').id)], limit = 1)
            self.env['mail.activity'].sudo().create({
                'res_model_id': self.env.ref('sale.model_sale_order').id,
                'res_id': order.id,
                'user_id': user_id.id,
                'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                'summary': _('Approval of Quotation : %s'%order.name),
                'note': _('<span>Hello, <b>%s</b>, just a quick reminder to review and approve the pending quotation <b>%s</b>.</br> Thanks!')%(user_id.name, order.name)
            })
            order.write({
                'state': 'sent',
                'approval_state': 'waiting_approval'
            })

    def action_confirm(self):
        if not self._context.get('from_button',False) and self.approval_state == 'approved':
            self.ensure_one()
            return {
                'type': 'ir.actions.act_window',
                'name': 'Invoice Policy',
                'view_mode': 'form',
                'res_model': 'invoice.policy.wizard',
                'domain': [],
                'context': {'is_sale':True},
                'target': 'new',
            }
        super_call = super(SaleOrder, self).action_confirm()
        for order in self:
            product_ids = order.order_line.filtered(lambda x:x.product_id.approval_request in ('draft','rejected'))
            if product_ids:
                raise ValidationError(_('Product must be Approved for the Order Confirmation. \n This Products is not Approved: %s')%('\n'.join(product_ids.mapped('product_id').mapped('name'))))
            # Sent email to customer based on the state
            order.send_mail_triggers_based_on_state()

        purchase_group = self.env.ref('purchase.group_purchase_user', raise_if_not_found=False)
        purchase_users = purchase_group.users if purchase_group else self.env['res.users']

        low_stock_products = []
        for line in self.order_line:
            if line.product_id.type == 'product' and line.product_uom_qty > line.product_id.qty_available:
                low_stock_products.append(f"{line.product_id.display_name}: Available {line.product_id.qty_available}, Required {line.product_uom_qty}")

        purchase_emails = ", ".join([user.email for user in purchase_users if user.email])
        if low_stock_products and purchase_emails:
            subject = _(f"Stock Alert: Low stock for Sale Order {self.name}")
            body = _(
                    f"Dear Purhase Manager,<br/><br/>"
                    f"The following products do not have enough stock for Sale Order {self.name}:<br/><ul>{''.join(f'<li>{p}</li>' for p in low_stock_products)}</ul><br/>"
                    f"A purchase order has been created for the required quantities. Please review it.<br/>"
                    f"Please review and take necessary actions.<br/><br/><br/>"
                    f"Thank You."
            )

            mail_values = {
                'subject': subject,
                'body_html': body,
                'email_to': purchase_emails,
                'email_from': self.env.user.email or self.env.company.email,
            }
            self.env['mail.mail'].create(mail_values).send()
        return super_call


    @api.onchange('partner_id','type')
    def _onchange_trainer_desc(self):
        for order in self:
            if order.partner_id.user_training_ids and order.type == 'training':
                product = self.env['product.product'].sudo().search([('type','not in',['service','product']),('categ_id.is_training','=',True)], limit=1)
                if product:
                    for trainer in order.partner_id.user_training_ids:
                        description = ''
                        description_sale = ''
                        trainer_name = ''
                        trainer_datetime = ''
                        trainer_venue = ''
                        trainer_type = ''
                        trainer_desc = ''
                        if trainer.name:
                            trainer_name = f"Trainer Name : {trainer.name}"
                        if trainer.datetime:
                            trainer_datetime = f"Trainer Date : {trainer.datetime.strftime('%d/%m/%Y')}\nTrainer Time : {trainer.datetime.strftime('%H:%M:%S')}"
                        if trainer.venue:
                            trainer_venue = f"Trainer Venue : {trainer.venue}"
                        if trainer.type:
                            trainer_type = f"Trainer Type : {trainer.type}"
                        if product.description_sale:
                            description_sale = f"{product.description_sale}"

                        trainer_desc = f"{trainer_name}\n{trainer_datetime}\n{trainer_venue}\n{trainer_type}"
                        if description_sale:
                            description += description_sale + '\n' + trainer_desc
                        else:
                            description += trainer_desc
                        self.update({'order_line': [(0,0,{'product_template_id': product.product_tmpl_id.id, 'product_id': product.id, 'name': description, 'product_uom_qty': 1})]})
                else:
                    pass
                    # line[0].update({'name': 'state no. of trainess : '})
            else:
                self.update({'order_line': False})

            if order.partner_id:
                config_note = self.env['fischerbell.configuration.note'].search([
                    ('type', '=', 'sale'),
                    ('partner_ids', 'in', [order.partner_id.id])  # Use a list to compare with a Many2many field
                ], limit=1)
                order.partner_note = config_note.note


    def _create_invoices(self, grouped=False, final=False, date=None):
        """ Create invoice(s) for the given Sales Order(s).

        :param bool grouped: if True, invoices are grouped by SO id.
            If False, invoices are grouped by keys returned by :meth:`_get_invoice_grouping_keys`
        :param bool final: if True, refunds will be generated if necessary
        :param date: unused parameter
        :returns: created invoices
        :rtype: `account.move` recordset
        :raises: UserError if one of the orders has no invoiceable lines.
        """
        if not self.env['account.move'].check_access_rights('create', False):
            try:
                self.check_access_rights('write')
                self.check_access_rule('write')
            except AccessError:
                return self.env['account.move']

        # 1) Create invoices.
        invoice_vals_list = []
        invoice_item_sequence = 0 # Incremental sequencing to keep the lines order on the invoice.
        for order in self:
            if order.type == 'loan':
                for pick in order.picking_ids:
                    if pick.is_return_loan:
                        pick.write({'state': 'cancel'})

            order = order.with_company(order.company_id).with_context(lang=order.partner_invoice_id.lang)

            invoice_vals = order._prepare_invoice()
            invoice_vals['narration'] = f"{'Terms and Conditions :'}"
            invoiceable_lines = order._get_invoiceable_lines(final)

            if not any(not line.display_type for line in invoiceable_lines):
                continue

            invoice_line_vals = []
            down_payment_section_added = False
            for line in invoiceable_lines:
                if not down_payment_section_added and line.is_downpayment:
                    # Create a dedicated section for the down payments
                    # (put at the end of the invoiceable_lines)
                    invoice_line_vals.append(
                        Command.create(
                            order._prepare_down_payment_section_line(sequence=invoice_item_sequence)
                        ),
                    )
                    down_payment_section_added = True
                    invoice_item_sequence += 1
                invoice_line_vals.append(
                    Command.create(
                        line._prepare_invoice_line(sequence=invoice_item_sequence)
                    ),
                )
                invoice_item_sequence += 1

            invoice_vals['invoice_line_ids'] += invoice_line_vals
            invoice_vals_list.append(invoice_vals)

        if not invoice_vals_list and self._context.get('raise_if_nothing_to_invoice', True):
            raise UserError(self._nothing_to_invoice_error_message())

        # 2) Manage 'grouped' parameter: group by (partner_id, currency_id).
        if not grouped:
            new_invoice_vals_list = []
            invoice_grouping_keys = self._get_invoice_grouping_keys()
            invoice_vals_list = sorted(
                invoice_vals_list,
                key=lambda x: [
                    x.get(grouping_key) for grouping_key in invoice_grouping_keys
                ]
            )
            for _grouping_keys, invoices in groupby(invoice_vals_list, key=lambda x: [x.get(grouping_key) for grouping_key in invoice_grouping_keys]):
                origins = set()
                payment_refs = set()
                refs = set()
                ref_invoice_vals = None
                for invoice_vals in invoices:
                    if not ref_invoice_vals:
                        ref_invoice_vals = invoice_vals
                    else:
                        ref_invoice_vals['invoice_line_ids'] += invoice_vals['invoice_line_ids']
                    origins.add(invoice_vals['invoice_origin'])
                    payment_refs.add(invoice_vals['payment_reference'])
                    refs.add(invoice_vals['ref'])
                ref_invoice_vals.update({
                    'ref': ', '.join(refs)[:2000],
                    'invoice_origin': ', '.join(origins),
                    'payment_reference': len(payment_refs) == 1 and payment_refs.pop() or False,
                })
                new_invoice_vals_list.append(ref_invoice_vals)
            invoice_vals_list = new_invoice_vals_list

        # 3) Create invoices.

        # As part of the invoice creation, we make sure the sequence of multiple SO do not interfere
        # in a single invoice. Example:
        # SO 1:
        # - Section A (sequence: 10)
        # - Product A (sequence: 11)
        # SO 2:
        # - Section B (sequence: 10)
        # - Product B (sequence: 11)
        #
        # If SO 1 & 2 are grouped in the same invoice, the result will be:
        # - Section A (sequence: 10)
        # - Section B (sequence: 10)
        # - Product A (sequence: 11)
        # - Product B (sequence: 11)
        #
        # Resequencing should be safe, however we resequence only if there are less invoices than
        # orders, meaning a grouping might have been done. This could also mean that only a part
        # of the selected SO are invoiceable, but resequencing in this case shouldn't be an issue.
        if len(invoice_vals_list) < len(self):
            SaleOrderLine = self.env['sale.order.line']
            for invoice in invoice_vals_list:
                sequence = 1
                for line in invoice['invoice_line_ids']:
                    line[2]['sequence'] = SaleOrderLine._get_invoice_line_sequence(new=sequence, old=line[2]['sequence'])
                    sequence += 1

        # Manage the creation of invoices in sudo because a salesperson must be able to generate an invoice from a
        # sale order without "billing" access rights. However, he should not be able to create an invoice from scratch.
        moves = self.env['account.move'].sudo().with_context(default_move_type='out_invoice').create(invoice_vals_list)

        # 4) Some moves might actually be refunds: convert them if the total amount is negative
        # We do this after the moves have been created since we need taxes, etc. to know if the total
        # is actually negative or not
        if final:
            moves.sudo().filtered(lambda m: m.amount_total < 0).action_switch_invoice_into_refund_credit_note()
        for move in moves:
            move.message_post_with_view(
                'mail.message_origin_link',
                values={'self': move, 'origin': move.line_ids.sale_line_ids.order_id},
                subtype_id=self.env['ir.model.data']._xmlid_to_res_id('mail.mt_note'))
        return moves


    @api.depends('purchase_order_count')
    def _compute_purchase_ref(self):
        self.purchase_ref = ''
        for order in self:
            purchase_order_line = self.env['purchase.order.line'].search([('sale_id','=',order.id)])
            if purchase_order_line:
                for po_line in purchase_order_line:
                    order.purchase_ref = po_line.order_id.name + ', '
            else:
                order.purchase_ref = ''

    def _get_terms_and_conditions(self):
        quo_terms = self.env['fischerbell.sale.terms.and.conditions'].search([('type','=','quotation')], limit=1)
        for order in self:
            if order.state == 'draft':
                order.terms_and_conditions = quo_terms.note
            else:
                if order.type == 'sale':
                    sale_terms = self.env['fischerbell.sale.terms.and.conditions'].search([('type','=','sale')], limit=1)
                    order.terms_and_conditions = sale_terms.note
                elif order.type == 'loan':
                    loan_terms = self.env['fischerbell.sale.terms.and.conditions'].search([('type','=','loan')], limit=1)
                    order.terms_and_conditions = loan_terms.note
                elif order.type == 'exchange':
                    exchange_terms = self.env['fischerbell.sale.terms.and.conditions'].search([('type','=','exchange')], limit=1)
                    order.terms_and_conditions = exchange_terms.note
                elif order.type == 'training':
                    training_terms = self.env['fischerbell.sale.terms.and.conditions'].search([('type','=','training')], limit=1)
                    order.terms_and_conditions = training_terms.note
                else:
                    replacement_terms = self.env['fischerbell.sale.terms.and.conditions'].search([('type','=','replacement')], limit=1)
                    order.terms_and_conditions = replacement_terms.note


    def _prepare_invoice(self):
        invoice_vals = super()._prepare_invoice()
        invoice_vals['sale_id'] = self.id
        invoice_vals['invoice_instruction'] = self.invoice_instruction
        return invoice_vals

    def action_view_purchase_order(self):
        self.ensure_one()
        purchase_order_ids = self._get_purchase_orders().ids
        action = {
            'res_model': 'purchase.order',
            'type': 'ir.actions.act_window',
        }
        if len(purchase_order_ids) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': purchase_order_ids[0],
            })
        else:
            action.update({
                'name': _("Purchase Order generated from %s", self.name),
                'domain': [('id', 'in', purchase_order_ids)],
                'view_mode': 'tree,form',
            })
        return action


    def _compute_billing_state(self):
        for order in self:
            order.billing_state = 'no_invoice'
            if order.invoice_status == 'invoiced':
                for inv in order.invoice_ids:
                    if inv.payment_state in ['paid','in_payment']:
                        order.billing_state = 'closed'
                    else:
                        order.billing_state = 'open'
            else:
                order.billing_state = 'open'

    def action_view_delivery(self):
        self.ensure_one()
        return {
            'name': 'Delivery',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form,calendar',
            'res_model': 'stock.picking',
            'domain': [('id', 'in', self.mapped('picking_ids').ids)],
            'context': {'picking_id': self.mapped('picking_ids').ids}
        }


    @api.onchange('partner_id')
    def onchange_partner_invoice_id(self):
        relation_ids = []
        child_ids = []
        if self.partner_invoice_id:
            self.invoice_instruction = self.partner_invoice_id.invoice_instruction
            relation_ids = [x.id for x in self.partner_id.child_ids]
            # return {'domain':{'partner_invoice_id': [('id', 'in', relation_ids)],}}
        if self.partner_shipping_id:
            self.delivery_instruction = self.partner_shipping_id.delivery_instruction
            child_ids = [x.id for x in self.partner_id.child_ids]
            # return {'domain': {'partner_shipping_id': [('id', 'in', child_ids)]}}
        if self.partner_invoice_id and not self.partner_invoice_id.street and not self.partner_invoice_id.street2 and not self.partner_invoice_id.city and not self.partner_invoice_id.state_id and not self.partner_invoice_id.zip and not self.partner_invoice_id.country_id:
            self.check_partner_address = False
        else:
            self.check_partner_address = True
        if not self.partner_invoice_id:
            self.check_partner_address = False
        return {'domain': {'partner_shipping_id': [('id', 'in', child_ids),('type','=','delivery')],'partner_invoice_id': [('id', 'in', relation_ids),('type','=','invoice')],'contact_person_id': [('id', 'in', child_ids),('type','=','contact')]}}

    # ---------------------------------------------------------------------------------
    # ----------------- SEND MAIL TRIGGERS --------------------------------------------
    # ---------------------------------------------------------------------------------

    def send_mail_triggers_based_on_state(self):
        """
            Send email based on the order's state
        """
        sale_draft_trigger_templ = self.env.ref('fischerbell_custom.email_template_sale_draft_trigger')
        sale_sale_state_trigger_templ = self.env.ref('fischerbell_custom.email_template_sale_sale_state_trigger')
        if self.state == 'draft':
            sale_draft_trigger_templ.send_mail(res_id=self.id)
        elif self.state == 'sale':
            sale_sale_state_trigger_templ.send_mail(res_id=self.id)
        return True

    def product_price(self):
        current_date = datetime.now()
        date_45_days_ago = current_date - timedelta(days=45)
        partner_invoice = self.env['account.move'].search([('partner_id', '=', self.partner_id.id), ('move_type', '=', 'out_invoice'), ('invoice_date', '<=', date_45_days_ago), ('payment_state', '!=', 'paid'), ('state', '!=', 'cancelled')])
        self.sale_reason = ''
        if any(line.price_unit <  line.product_id.list_price for line in self.order_line):
            self.is_approved_sale = True
            self.sale_reason = 'Sale price is below the product list price!'
        if len(partner_invoice) > 0:
            self.is_approved_sale = True
            self.sale_reason  += 'Partner has overdue invoices! '
        if self.partner_id.is_contact_created:
            self.is_approved_sale = True
            self.sale_reason  += 'Customer is already existing!'


    @api.model
    def create(self, vals):
        name = ''
        partner = False
        if vals.get('partner_invoice_id'):
            partner = self.env['res.partner'].search([('id','=',vals.get('partner_invoice_id'))],limit=1)

            if partner:
                name = name + "\n" + partner._display_address(without_company=True)
                vals['partner_invoice_address'] = name

        res = super().create(vals)
        res.product_price()
        # Send email to customer
        res.send_mail_triggers_based_on_state()
        return res

    @api.depends('picking_ids', 'picking_ids.state')
    def _compute_delivery_status(self):
        super(SaleOrder, self)._compute_delivery_status()
        sale_picking_pending_state_trigger_templ = self.env.ref('fischerbell_custom.email_template_sale_picking_pending_state_trigger')
        sale_picking_done_state_trigger_templ = self.env.ref('fischerbell_custom.email_template_sale_picking_done_state_trigger')
        for order in self:
            if order.delivery_status == 'pending':
                sale_picking_pending_state_trigger_templ.send_mail(res_id=order.id)
            elif order.delivery_status == 'full':
                order.scheduled_delivery_date = fields.datetime.now()
                sale_picking_done_state_trigger_templ.send_mail(res_id=order.id)

    def write(self, vals):
        name = ''
        partner = False
        if vals.get('partner_invoice_id'):
            partner = self.env['res.partner'].search([('id','=',vals.get('partner_invoice_id'))],limit=1)

            for order in self:
                if partner:
                    name = name + "\n" + partner._display_address(without_company=True)
                    order.partner_invoice_address = name
                    order.check_partner_address = True
                if not order.partner_invoice_address:
                    order.check_partner_address = False

        for order in self:
            if vals.get('state') == 'sale' and order.approval_state == 'no':
                vals['approval_state'] = 'waiting_approval'
                vals['state'] = 'waiting_approval'

            if vals.get('state') == 'cancel':
                vals['approval_state'] = 'reject'
                for mrp in order.mrp_production_ids:
                    mrp.state = 'cancel'

            if vals.get('state') == 'draft':
                vals['approval_state'] = 'no'

            if vals.get('state') == 'sent' and not self.is_approved_sale:
                vals['state'] = 'approve'
                vals['partner_request_state'] = 'approved'
                vals['approval_state'] = 'approved'
                vals['reviewed_by'] = self.env.user.id


        res = super().write(vals)
        if vals.get('order_line'):
            self.product_price()
        for order in self:
            if vals.get('tag_ids'):
                for pick in order.picking_ids:
                    pick.tag_ids = vals['tag_ids']

        return res


    @api.depends('type','picking_ids', 'picking_ids.state')
    def _compute_loan_state(self):
        for order in self:
            order.loan_date = False
            order.loan_state = 'not_loan'
            if order.type == 'loan' and order.picking_ids:
                for pick in order.picking_ids:
                    if pick.is_return_loan and pick.state != 'done' and pick.picking_type_code == 'incoming':
                        order.loan_state = 'open'
                    elif pick.is_return_loan and pick.state == 'done' and pick.picking_type_code == 'incoming':
                        order.loan_state = 'closed'
                        order.loan_date = fields.Date.today()
                    else:
                        order.loan_state = 'open'
            elif order.type == 'loan' and not order.picking_ids:
                order.loan_state = 'open'
            else:
                order.loan_state = 'not_loan'



    def create_loan_orders(self):
        for sale in self:
            sale_id = sale.create({
                'sale_id': sale.id,
                'partner_id': sale.partner_id.id,
                'partner_invoice_id': sale.partner_invoice_id.id,
                'partner_shipping_id': sale.partner_shipping_id.id,
                'pricelist_id': sale.pricelist_id.id,
                'type': 'loan',
                'state': 'draft',
            })

        return


    @api.depends('loan_ids')
    def _compute_loan_ids(self):
        for order in self:
            loan_ids = list(filter(lambda x: (x.type == 'loan'), order.loan_ids))
            order.loan_order_count = len(loan_ids)


    def action_view_loan_order(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Loan Orders',
            'view_mode': 'tree,form',
            'res_model': 'sale.order',
            'domain': [('sale_id', '=', self.id),('type','=','loan')],
            'context': {'default_sale_id':self.id, 'default_type': 'loan', 'form_view_ref': 'sale.view_order_form', 'tree_view_ref':'sale.view_order_tree'},
            'tag': 'reload'
        }

    def get_report_name(self):
        self.ensure_one()
        return '%s - %s %s'%(datetime.now().year,self.name or '',self.partner_id.parent_id.name or self.partner_id.name)

    def get_order_template_subject(self):
        self.ensure_one()
        pass
        
    # Set first followup date in order cron.
    def cron_set_followup_date(self):
        for rec in self.search([
                ('state', '=', 'draft'),  # Assuming 'draft' is the status of quotations
                ('date_order', '<=', fields.Date.today() - timedelta(days=7)),
                ('first_followup_date', '=', False)
            ]):
            rec.first_followup_date = datetime.now()

    def cron_set_sec_followup_date(self):
        for rec in self.search([
                ('state', '=', 'draft'),  # Assuming 'draft' is the status of quotations
                ('first_followup_date', '!=', False),
                ('first_followup_date', '<=', fields.Date.today() - timedelta(days=7))
            ]):
            rec.sec_followup_date = datetime.now()

    def cron_reminder_customer_to_status(self):
        user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
        today = user_tz.localize(fields.Datetime.from_string(fields.Date.context_today(self))) - timedelta(days=7)
        date_start = today.astimezone(pytz.timezone('UTC'))
        date_stop = date_start + timedelta(days=1, seconds=-1)
        for rec in self.env['sale.order'].search([
                                    ('state', '!=', 'sale'),
                                    ('create_date', '>=', date_start),
                                    ('create_date', '<=', date_stop),
                ]):
            if rec:
                display_message = """
                                        <p>We noticed that your order with reference number """ + rec.name + """ is still pending confirmation. 
                                        If you have any inquiries or concerns regarding this order, please feel free to reach out. 
                                        We are here to assist you and ensure a smooth process.</p>
                                        """
                subject = (f""" Inquiry about Order  %s  Confirmation Status""" % rec.name)
                email_to = rec.partner_id.email
                mails = {
                    'subject': subject,
                    'email_from': self.env.user.email_formatted,
                    'email_to': email_to,
                    'body_html': display_message,
                    'auto_delete': False,
                }
                mail = self.env['mail.mail'].create(mails)
                mail.send()
                
    def cron_reminder_processing_team_to_followup(self):
        user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
        today = user_tz.localize(fields.Datetime.from_string(fields.Date.context_today(self))) - timedelta(days=14)
        date_start = today.astimezone(pytz.timezone('UTC'))
        date_stop = date_start + timedelta(days=1, seconds=-1)
        for rec in self.env['sale.order'].search([
                                    ('state', '!=', 'sale'),
                                    ('create_date', '>=', date_start),
                                    ('create_date', '<=', date_stop),
                ]):
            if rec:
                display_message = """
                                        <p>For this order """ + rec.name + """, since the customer has not responded, kindly proceed with a follow-up, meeting, or phone call to engage with the customer.</p>
                                        """
                subject = (f""" Action Required for Quotation %s Customer Follow-Up Needed """ % rec.name)
                email_to = rec.user_id.email
                mails = {
                    'subject': subject,
                    'email_from': self.env.user.email_formatted,
                    'email_to': email_to,
                    'body_html': display_message,
                    'auto_delete': False,
                }
                mail = self.env['mail.mail'].create(mails)
                mail.send()
    
    def action_draft(self):
        res = super().action_draft()
        line_ids = self.order_line
        line_ids.write({'approval_state':False})
        return res
    
    def create_sequance_contact(self):
        for sale in self:
                sale.write({'partner_request_state':'pending',
                            'is_requested':True})

    def request_approved(self):
        for sale in self:
            if not sale.partner_id.is_contact_created:
                code = self.env['ir.sequence'].next_by_code('res.partner.customer') or _('New')
                sale.partner_id.write({
                    'code': code,
                    'is_contact_created': True,
                    'customer_rank': sale.partner_id.customer_rank,
                    'property_product_pricelist': sale.partner_id.property_product_pricelist.id if sale.partner_id.property_product_pricelist else False
                })
            sale.write({
                'partner_request_state': 'approved',
                'partner_id': sale.partner_id.id
            })

    def request_rejected(self):
        for sale in self:
            sale.write({'partner_request_state':'rejected'})
    
    @api.model
    def merge_quotations(self):
        active_ids = self.env.context.get('active_ids', [])
        if len(active_ids) < 2:
            raise ValidationError(_("You must select at least two sale orders to merge."))
        sale_orders = self.browse(active_ids)
        partner_ids = sale_orders.mapped('partner_id.id')
        if len(set(partner_ids)) > 1:
            raise ValidationError(_("Selected sale orders must belong to the same customer."))
        draft_orders = sale_orders.filtered(lambda so: so.state == 'draft')
        if len(draft_orders) != len(sale_orders):
            raise ValidationError(_("All selected sale orders must be in the Quotation."))
        latest_order = draft_orders.sorted(lambda so: so.create_date, reverse=True)[0]
        for order in draft_orders - latest_order:
            for line in order.order_line:
                existing_line = latest_order.order_line.filtered(lambda l: l.product_id == line.product_id)
                if existing_line:
                    existing_line.write({'product_uom_qty': existing_line.product_uom_qty + line.product_uom_qty,
                                        'price_unit':line.price_unit})
                    existing_line._compute_amount()
                else:
                    line.copy(default={'order_id': latest_order.id})
                    line._compute_amount()
            order.action_cancel()
        return {
                  'type': 'ir.actions.act_window',
                  'name': _('Quotation'),
                  'res_model': 'sale.order',
                  'view_mode': 'form',
                  'view_type': 'form',
                  'res_id':latest_order.id,
              }
    def create_sub_order(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sale Order Lines',
            'view_mode': 'tree',
            'res_model': 'sale.order.line',
            'domain': [('order_id', '=', self.id),('state','=','draft')],
            'context':{'create':False,'edit':False,'is_suborder':True},
            'target':'new'
        }

    def action_view_saleorder(self):
        self.sub_order_count = len(self.sub_order_ids.ids)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sub Order',
            'view_mode': 'tree,form',
            'res_model': 'sale.order',
            'domain': [('id', 'in', self.sub_order_ids.ids)],
            'context':{'create':False,'edit':False},
            'target':'current'
        }

    @api.model
    def check_delivery_lead_time(self):
        # Get the number of days from settings
        days_to_check = int(self.env['ir.config_parameter'].sudo().get_param(
            'sale_order_lead_time_notification.delivery_lead_time_days', default=5))
        
        # Get today's date and the date 'days_to_check' days from now
        today = datetime.today().date()
        delivery_date_threshold = today + timedelta(days=days_to_check)
        
        # Search for sale orders with delivery date within the configured number of days
        sale_orders = self.search([
            ('state', '=', 'sale'),  # Sale order should be confirmed
            ('scheduled_delivery_date', '<=', delivery_date_threshold)
        ])

        # Check stock availability and send email if not enough stock
        for order in sale_orders:
            not_enough_stock = False
            products_info = ""
            
            for line in order.order_line:
                product = line.product_id
                qty_available = product.qty_available
                qty_required = line.product_uom_qty
                
                if qty_available < qty_required:
                    not_enough_stock = True
                    products_info += f"{product.display_name}: Required {qty_required}, Available {qty_available}\n"

            if not_enough_stock:
                # Send email to the "Delivery Lead Time Notification Group"
                notification_group = self.env.ref('fischerbell_custom.group_delivery_lead_time_notification')
                if notification_group:
                    email_to = ','.join(user.email for user in notification_group.users if user.email)
                    if email_to:
                        # Send email
                        mail_content = f"""
                            <p>Dear Team,</p>
                            <p>The following sale order has a delivery within {days_to_check} days, but there isn't enough stock available:</p>
                            <p>Sale Order: <strong>{order.name}</strong></p>
                            <pre>{products_info}</pre>
                            <p>Please review and take the necessary action.</p>
                        """
                        mail_values = {
                            'subject': f"Delivery Alert for Sale Order {order.name}",
                            'body_html': mail_content,
                            'email_to': email_to,
                        }
                        self.env['mail.mail'].create(mail_values).send()

class SaleOrderLine(models.Model):
    _name = 'sale.order.line'
    _inherit = ['sale.order.line','mail.thread', 
                'mail.activity.mixin']

    product_code = fields.Char('Product Code', related="product_template_id.default_code")
    customer_id = fields.Many2one('res.partner', 'Customer', related="order_id.partner_id")
    customer_sku = fields.Char('Customer SKU')
    bp_code = fields.Char('BP Code')
    batch_number = fields.Char('Batch Number')
    use_bp_code = fields.Boolean('Use BP code',related="product_template_id.use_bp_code")
    use_product_batch_number = fields.Boolean('Use Product Batch Number', related="product_template_id.use_product_batch_number")
    lead_time_stock = fields.Char('Lead Time Stock', compute="_compute_lead_time_stock", store=True)
    terms_and_condition_ids = fields.Many2many('fischerbell.product.terms.and.conditions', string="Terms & Conditions", related="product_id.terms_and_condition_ids")
    last_invoice_date = fields.Datetime(string="Last Invoice Date",compute="_compute_get_last_invoice_date")
    last_invoice_price = fields.Float(string="Last Invoice Price",compute="_compute_get_last_invoice_date")
    last_price = fields.Float('Last Order Price', compute="_compute_last_order_price", store=True)
    picking_id = fields.Many2one('stock.picking', 'Picking')
    product_detail_sheet_url = fields.Char(related="product_id.product_detail_sheet_url")
    request_price = fields.Float('Requested Price', readonly=True)
    is_requested = fields.Boolean('Is Update Requested',readonly=True)
    is_request_updated = fields.Boolean('Is Request Updated',readonly=True)
    price_unit = fields.Float(
        string="Unit Price",
        compute='_compute_price_unit',
        digits='Product Price',
        store=True, readonly=False, required=True, precompute=True, tracking=True)
    approval_state = fields.Selection([('pending','Pending'),('approved','Approved'),
                                        ('rejected','Rejected')
                                        ], string="Approval", 
                                        tracking=True, copy=False)
    last_order_date = fields.Datetime('Last Order Date', compute='_compute_last_order_price')
    last_sale_id = fields.Many2one('sale.order', string='Last Order', readonly=True, compute='_compute_last_order_price')
    change_reason = fields.Text(string="Reason for Change", readonly=True)


    @api.depends('customer_id','product_id','state')
    def _compute_last_order_price(self):
        for price in self:
            last_order = self.search([('id','!=', price._origin.id),('customer_id','=', price.customer_id.id),
                                    ('product_id','=',price.product_id.id ),('state','=','sale'),('id','<',price._origin.id)],
                                    limit=1, order='id desc')
            price.write(dict(last_price = last_order.price_unit  * last_order.product_uom_qty if last_order else 0,
                            last_order_date = last_order and last_order.order_id.date_order or False,
                            last_sale_id = last_order and last_order.order_id.id or False))

    def _compute_get_last_invoice_date(self):
        move_line_obj = self.env['account.move.line']
        for rec in self:
            invoice_ids = move_line_obj.search([('product_id','=',rec.product_id.id),('move_id.state','=','posted')]).mapped('move_id')
            rec.last_invoice_date = False
            rec.last_invoice_price = False
            if invoice_ids:
                last_invoice_date = min(invoice_ids.mapped('create_date'))
                last_invoice_id = self.env['account.move'].search([('create_date','=',last_invoice_date)])
                rec.last_invoice_date = last_invoice_id.create_date
                rec.last_invoice_price = move_line_obj.search([('product_id','=',rec.product_id.id),('move_id','=',last_invoice_id.id)],limit=1).price_unit

    @api.depends('product_template_id.virtual_available')
    def _compute_lead_time_stock(self):
        self.lead_time_stock = ''
        for line in self:
            if line.product_template_id.virtual_available > 0:
                line.lead_time_stock = 'Ex-Stock'
            else:
                line.lead_time_stock = 'Indent'


    @api.onchange('product_template_id')
    def onchange_sale_customer_sku(self):
        if self.customer_id and self.product_template_id and self.product_template_id.use_customer_sku:
            customer_sku = ''
            for line in self.product_template_id.customer_sku_ids:
                if line.customer_id == self.customer_id and line.customer_sku:
                    customer_sku = line.customer_sku
            if customer_sku:
                self.customer_sku = customer_sku
            else:
                self.customer_sku = ''
        else:
            self.customer_sku = ''

        if self.product_template_id and self.product_template_id.use_bp_code and self.product_template_id.bp_code:
            self.bp_code = self.product_template_id.bp_code
        else:
            self.bp_code = ''


    @api.onchange('price_unit')
    def onchange_price_unit(self):
        if self.price_unit:
            if self.price_unit > self.product_template_id.max_price:
                raise ValidationError("Sales price is greater than maximal price")
            if self.price_unit < self.product_template_id.min_price:
                raise ValidationError("Sales price is less than minimal price")
    
    def update_request_price(self):
        for line in self:
            if line.is_requested:
                line.update({'price_unit':line.request_price,
                            'is_request_updated':True,
                            'approval_state':'approved'})
            else:
                raise ValidationError(_('This Line is not requested for the Update Price, Order Ref:% and Product:%s')%(line.order_id.name,line.product_id.name))
            
    def reject_request(self):
        for line in self:
            line.write({'approval_state':'rejected','is_request_updated':True})

    def create_order(self):
        context = dict(self._context)
        sale_id = self.env['sale.order.line'].browse(context.get('active_ids')).mapped('order_id')[0]
        sub_order_id = sale_id.copy({'order_line':False,'sub_order_ids':False})
        sale_id.mapped('order_line').filtered(lambda x:x.id in context.get('active_ids')).write({'order_id':sub_order_id and sub_order_id.id})
        sale_id.write({'sub_order_ids':[(4,sub_order_id.id)]})
        return True
    
    @api.depends('product_id')
    def _compute_name(self):
        res = super(SaleOrderLine,self)._compute_name()
        for line in self:
            if line.product_id :
                bom_ids = self.env['mrp.bom'].sudo().search([
                    '|',
                    ('product_id', '=', line.product_id.id),
                    ('product_tmpl_id', '=', line.product_template_id.id),
                    ('type', '=', 'phantom')
                ], limit=1, order='product_id desc')
                if bom_ids:
                    # Fetch the components of the BoM
                    component_lines = []
                    for idx, component in enumerate(bom_ids.bom_line_ids, start=1):
                        component_lines.append(f"{idx}: {component.product_id.display_name}")
                    # Append components to the name
                    components_description = "\n".join(component_lines)
                    line.name = f"{line.name}\n{_('Components:')}\n{components_description}"
        return res