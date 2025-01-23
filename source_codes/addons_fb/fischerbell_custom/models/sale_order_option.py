# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import defaultdict
from odoo import api,fields, models, _
from odoo.tools import float_is_zero, float_compare, float_round


class SaleOrderOption(models.Model):
    _inherit = 'sale.order.option'
    
    currency_id = fields.Many2one(
        related='order_id.currency_id',
        depends=['order_id.currency_id'],
        store=True, precompute=True)
    customer_sku = fields.Char('Customer SKU')
    customer_id = fields.Many2one('res.partner', 'Customer', related="order_id.partner_id")
    company_id = fields.Many2one(
        related='order_id.company_id',
        store=True, index=True, precompute=True)
    product_code = fields.Char('Product Code', related="product_id.default_code")
    terms_and_condition_ids = fields.Many2many('fischerbell.product.terms.and.conditions', string="Terms & Conditions", related="product_id.terms_and_condition_ids")
    last_price = fields.Float('Last Order Price', compute="_compute_last_order_price", store=True)
    last_order_date = fields.Datetime('Last Order Date', compute='_compute_last_order_price')
    last_sale_id = fields.Many2one('sale.order', string='Last Order', readonly=True, compute='_compute_last_order_price')
    state = fields.Selection(
        related='order_id.state',
        string="Order Status",
        copy=False, store=True, precompute=True)
    display_type = fields.Selection(
        selection=[
            ('line_section', "Section"),
            ('line_note', "Note"),
        ],
        default=False)
    tax_id = fields.Many2many(
        comodel_name='account.tax',
        string="Taxes",
        compute='_compute_tax_id',
        store=True, readonly=False, precompute=True,
        context={'active_test': False},
        check_company=True)
    approval_state = fields.Selection([('pending','Pending'),('approved','Approved'),
        ('rejected','Rejected')
        ], string="Approval", 
        tracking=True, copy=False)
    price_subtotal = fields.Monetary(
        string="Subtotal",
        compute='_compute_amount',
        store=True, precompute=True)
    price_tax = fields.Float(
        string="Total Tax",
        compute='_compute_amount',
        store=True, precompute=True)
    price_total = fields.Monetary(
        string="Total",
        compute='_compute_amount',
        store=True, precompute=True)
    product_packaging_id = fields.Many2one(
        comodel_name='product.packaging',
        string="Packaging",
        compute='_compute_product_packaging_id',
        store=True, readonly=False, precompute=True,
        domain="[('sales', '=', True), ('product_id','=',product_id)]",
        check_company=True)
    product_packaging_qty = fields.Float(
        string="Packaging Quantity",
        compute='_compute_product_packaging_qty',
        store=True, readonly=False, precompute=True)
    product_uom = fields.Many2one(
        comodel_name='uom.uom',
        string="Unit of Measure",
        compute='_compute_product_uom',
        store=True, readonly=False, precompute=True, ondelete='restrict',
        domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_qty = fields.Float(
        string="Quantity",
        compute='_compute_product_uom_qty',
        digits='Product Unit of Measure', default=1.0,
        store=True, readonly=False, required=True, precompute=True)
    product_detail_sheet = fields.Many2one('ir.attachment',string="Detail sheet")
    product_detail_sheet_url = fields.Char(string='Sheet Url', compute="_compute_sheet_url")
    child_id = fields.Many2one("res.partner",string="Employee id")
    child_name = fields.Char("Employee name")
    product_template_id = fields.Many2one(
        string="Product Template",
        comodel_name='product.template',
        compute='_compute_product_template_id',
        readonly=False,
        search='_search_product_template_id',
        # previously related='product_id.product_tmpl_id'
        # not anymore since the field must be considered editable for product configurator logic
        # without modifying the related product_id when updated.
        domain=[('sale_ok', '=', True)])
    bp_code = fields.Char('BP Code')
    pricing_id = fields.Many2one('product.pricing',
            compute='_compute_pricing', store=True, precompute=True)
    route_id = fields.Many2one('stock.route', string='Route', 
        domain=[('sale_selectable', '=', True)], ondelete='restrict', check_company=True)
    lead_time_stock = fields.Char('Lead Time Stock', compute="_compute_lead_time_stock", store=True)
    task_id = fields.Many2one(
        'project.task', 'Generated Task',
        index=True, copy=False)
    
    @api.depends('product_template_id.virtual_available')
    def _compute_lead_time_stock(self):
        self.lead_time_stock = ''
        for line in self:
            if line.product_template_id.virtual_available > 0:
                line.lead_time_stock = 'Ex-Stock'
            else:
                line.lead_time_stock = 'Indent'

    @api.depends('product_id', 'order_id.recurrence_id')
    def _compute_pricing(self):
        # search pricing_ids for each variant in self
        available_pricing_ids = self.env['product.pricing'].search([
            ('product_template_id', 'in', self.product_id.product_tmpl_id.ids),
            ('recurrence_id', 'in', self.order_id.recurrence_id.ids),
            '|',
            ('product_variant_ids', 'in', self.product_id.ids),
            ('product_variant_ids', '=', False),
            '|',
            ('pricelist_id', 'in', self.order_id.pricelist_id.ids),
            ('pricelist_id', '=', False)
        ])
        for line in self:
            if not line.product_id.recurring_invoice:
                line.pricing_id = False
                continue
            line.pricing_id = available_pricing_ids.filtered(
                lambda pricing:
                    line.product_id.product_tmpl_id == pricing.product_template_id and (
                        line.product_id in pricing.product_variant_ids or not pricing.product_variant_ids
                    ) and (line.order_id.pricelist_id == pricing.pricelist_id or not pricing.pricelist_id)
            )[:1]

    @api.depends('product_id')
    def _compute_product_template_id(self):
        for line in self:
            line.product_template_id = line.product_id.product_tmpl_id
    
    def _search_product_template_id(self, operator, value):
        return [('product_id.product_tmpl_id', operator, value)]
    
    def _compute_sheet_url(self):
        base_url = self.env.company.get_base_url()
        for rec in self:
            if rec.product_detail_sheet:
                access_token = rec.product_detail_sheet.generate_access_token()
                url = f"{base_url}/web/content/?model=ir.attachment&id={rec.product_detail_sheet.id}&filename_field=name&access_token={access_token[0]}&field=datas&download=true"
                rec.product_detail_sheet_url = url
            else:
                rec.product_detail_sheet_url = ''
                    
    @api.depends('product_id')
    def _compute_product_uom(self):
        for line in self:
            if not line.product_uom or (line.product_id.uom_id.id != line.product_uom.id):
                line.product_uom = line.product_id.uom_id

    @api.depends('product_id', 'product_uom_qty', 'product_uom')
    def _compute_product_packaging_id(self):
        for line in self:
            # remove packaging if not match the product
            if line.product_packaging_id.product_id != line.product_id:
                line.product_packaging_id = False
            # Find biggest suitable packaging
            if line.product_id and line.product_uom_qty and line.product_uom:
                line.product_packaging_id = line.product_id.packaging_ids.filtered(
                    'sales')._find_suitable_product_packaging(line.product_uom_qty, line.product_uom) or line.product_packaging_id
                
    @api.depends('product_packaging_id', 'product_uom', 'product_uom_qty')
    def _compute_product_packaging_qty(self):
        for line in self:
            if not line.product_packaging_id:
                line.product_packaging_qty = False
            else:
                packaging_uom = line.product_packaging_id.product_uom_id
                packaging_uom_qty = line.product_uom._compute_quantity(line.product_uom_qty, packaging_uom)
                line.product_packaging_qty = float_round(
                    packaging_uom_qty / line.product_packaging_id.qty,
                    precision_rounding=packaging_uom.rounding)
                
    @api.depends('display_type', 'product_id', 'product_packaging_qty')
    def _compute_product_uom_qty(self):
        for line in self:
            if line.display_type:
                line.product_uom_qty = 0.0
                continue

            if not line.product_packaging_id:
                continue
            packaging_uom = line.product_packaging_id.product_uom_id
            qty_per_packaging = line.product_packaging_id.qty
            product_uom_qty = packaging_uom._compute_quantity(
                line.product_packaging_qty * qty_per_packaging, line.product_uom)
            if float_compare(product_uom_qty, line.product_uom_qty, precision_rounding=line.product_uom.rounding) != 0:
                line.product_uom_qty = product_uom_qty

    @api.depends('customer_id','product_id','state')
    def _compute_last_order_price(self):
        for price in self:
            last_order = self.search([('id','!=', price._origin.id),('customer_id','=', price.customer_id.id),
                                    ('product_id','=',price.product_id.id ),('state','=','sale'),('id','<',price._origin.id)],
                                    limit=1, order='id desc')
            price.write(dict(last_price = last_order.price_unit  * last_order.product_uom_qty if last_order else 0,
                            last_order_date = last_order and last_order.order_id.date_order or False,
                            last_sale_id = last_order and last_order.order_id.id or False))
    
    @api.depends('product_id', 'company_id')
    def _compute_tax_id(self):
        taxes_by_product_company = defaultdict(lambda: self.env['account.tax'])
        lines_by_company = defaultdict(lambda: self.env['sale.order.option'])
        cached_taxes = {}
        for line in self:
            lines_by_company[line.company_id] += line
        for product in self.product_id:
            for tax in product.taxes_id:
                taxes_by_product_company[(product, tax.company_id)] += tax
        for company, lines in lines_by_company.items():
            for line in lines.with_company(company):
                taxes = taxes_by_product_company[(line.product_id, company)]
                if not line.product_id or not taxes:
                    # Nothing to map
                    line.tax_id = False
                    continue
                fiscal_position = line.order_id.fiscal_position_id
                cache_key = (fiscal_position.id, company.id, tuple(taxes.ids))
                if cache_key in cached_taxes:
                    result = cached_taxes[cache_key]
                else:
                    result = fiscal_position.map_tax(taxes)
                    cached_taxes[cache_key] = result
                # If company_id is set, always filter taxes by the company
                line.tax_id = result
    
    def _convert_to_tax_base_line_dict(self):
        """ Convert the current record to a dictionary in order to use the generic taxes computation method
        defined on account.tax.

        :return: A python dictionary.
        """
        self.ensure_one()
        return self.env['account.tax']._convert_to_tax_base_line_dict(
            self,
            partner=self.order_id.partner_id,
            currency=self.order_id.currency_id,
            product=self.product_id,
            taxes=self.tax_id,
            price_unit=self.price_unit,
            quantity=self.product_uom_qty,
            discount=self.discount,
            price_subtotal=self.price_subtotal,
        )
    
    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            tax_results = self.env['account.tax']._compute_taxes([line._convert_to_tax_base_line_dict()])
            totals = list(tax_results['totals'].values())[0]
            amount_untaxed = totals['amount_untaxed']
            amount_tax = totals['amount_tax']

            line.update({
                'price_subtotal': amount_untaxed,
                'price_tax': amount_tax,
                'price_total': amount_untaxed + amount_tax,
            })