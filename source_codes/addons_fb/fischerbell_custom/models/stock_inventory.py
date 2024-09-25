# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.addons.base.models.ir_model import MODULE_UNINSTALL_FLAG
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo.tools import float_compare, float_is_zero


class Inventory(models.Model):
    _name = "stock.inventory"
    _description = "Inventory"
    _order = "date desc, id desc"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        'Inventory Reference', default="Inventory",
        readonly=True, required=True)
    date = fields.Datetime(
        'Inventory Date',
        readonly=True, required=True,
        default=fields.Datetime.now,
        help="If the inventory adjustment is not validated, date at which the theoritical quantities have been checked.\n"
             "If the inventory adjustment is validated, date at which the inventory adjustment has been validated.")
    company_id = fields.Many2one(
        'res.company', 'Company',
        index=True, required=True,
        default=lambda self: self.env.company)
    location_ids = fields.Many2many(
        'stock.location', string='Locations',
        check_company=True,
        domain="[('company_id', '=', company_id), ('usage', 'in', ['internal', 'transit'])]")
    product_ids = fields.Many2many(
        'product.product', string='Products', check_company=True,
        domain="[('type', '=', 'product'), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        help="Specify Products to focus your inventory on particular Products.")
    state = fields.Selection(string='Status', selection=[
        ('draft', 'Draft'),
        ('cancel', 'Cancelled'),
        ('confirm', 'In Progress'),
        ('done', 'Validated')],
        copy=False, index=True, readonly=True, tracking=True,
        default='draft')

    def open_product_quant(self):
        # self = self._set_view_context()
        # self._quant_tasks()
        ctx = dict(self.env.context or {})
        ctx['no_at_date'] = True
        ctx['inventory_id'] = self.id
        if self.user_has_groups('stock.group_stock_user') and not self.user_has_groups('stock.group_stock_manager'):
            ctx['search_default_my_count'] = True

        domain  = [('location_id.usage', 'in', ['internal', 'transit'])]
        if self.product_ids:
        	domain += [('product_id', 'in', self.product_ids.ids)]
        if self.location_ids:
        	domain += [('location_id', 'in', self.location_ids.ids)]
        action = {
            'name': _('Inventory Adjustments'),
            'view_mode': 'list',
            'view_id': self.env.ref('stock.view_stock_quant_tree_inventory_editable').id,
            'res_model': 'stock.quant',
            'type': 'ir.actions.act_window',
            'context': ctx,
            'domain': domain,
            'help': """
                <p class="o_view_nocontent_smiling_face">
                    {}
                </p><p>
                    {} <span class="fa fa-long-arrow-right"/> {}</p>
                """.format(_('Your stock is currently empty'),
                           _('Press the CREATE button to define quantity for each product in your stock or import them from a spreadsheet throughout Favorites'),
                           _('Import')),
        }
        return action

    def action_view_related_move_lines(self):
        self.ensure_one()
        move_ids = self.env['stock.move'].search([('inventory_id', '=', self.id)])
        domain = [('move_id', 'in', move_ids.ids)]
        action = {
            'name': _('Product Moves'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.move.line',
            'view_type': 'list',
            'view_mode': 'list,form',
            'domain': domain,
        }
        return action


    def action_validate(self):
        self.state = 'done'