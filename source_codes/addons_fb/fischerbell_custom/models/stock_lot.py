# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from operator import attrgetter
from re import findall as regex_findall, split as regex_split

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class StockLot(models.Model):
	_inherit = 'stock.lot'

	tracking = fields.Selection([
		('serial', 'By Unique Serial Number'),
		('lot', 'By Batch'),
		('none', 'No Tracking')],
		string="Tracking", required=True, default='none',
		compute='_compute_get_tracking', store=True)
	attribute_one = fields.Html('Attribute 1')
	attribute_two = fields.Html('Attribute 2')
	manufacturing_date = fields.Date('manufacturing date',compute='_compute_get_manufacturing_date')

	@api.depends('product_id.tracking')
	def _compute_get_tracking(self):
		self.tracking = 'none'
		for stock_lot in self:
			if stock_lot.product_id.tracking:
				stock_lot.tracking = stock_lot.product_id.tracking
			else:
				stock_lot.tracking = 'none'


	@api.depends('manufacturing_date')
	def _compute_get_manufacturing_date(self):
		for record in self:
			move_line = self.env['stock.move.line'].search([('lot_id', '=', record.id)], limit=1)
			if move_line:
				record.manufacturing_date = move_line.manufacturing_date
			else:
				record.manufacturing_date = False

	def product_expiration_email(self):
		lot_ids = self.env['stock.lot'].search([('alert_date', '!=', False)])
		inv_user_id = self.env['res.users'].search([
            ('groups_id', 'in', [self.env.ref('stock.group_stock_manager').id]),
            ('id', '!=', self.env.ref('base.user_admin').id)
        ], limit=1)
		list_data = []
		record_found = False
		for record in lot_ids:
			quant_ids = self.env['stock.quant'].search([
                ('lot_id', '=', record.id),
                ('location_id.usage', '=', 'internal')
            ]).filtered(lambda x: x.inventory_quantity_auto_apply > 0)
			if quant_ids and record.alert_date:
				reminder_date = record.alert_date.date()
				if reminder_date == fields.date.today():
					record_found = True
					list_data.append({
                        'product_name': record.product_id.name,
                        'lot_name': record.name,
                        'quantity': sum(quant_ids.mapped('quantity')),
                        'expiration_date':record.expiration_date.date()
                        })
		# Prepare email body
		if record_found:
			rows = ''.join([
                f"""<tr style="text-align:center">
                        <td>{item['product_name']}</td>
                        <td>{item['lot_name']}</td>
                        <td>{item['expiration_date']}</td>
                        <td>{item['quantity']}</td>
                    </tr>""" for item in list_data
            ])
			body = f"""Hello {inv_user_id.partner_id.name},<br><br>
                        <p>We are writing to inform you that the following products will expire and need your attention:</p><br><br>
                        <table border="1" cellpadding="5" cellspacing="0" width="50%">
                            <tr>
                                <th>Product</th>
                                <th>Lot</th>
                                <th>Expiration Date</th>
                                <th>Quantity</th>
                            </tr>
                            {rows}
                        </table>
                        <br>
                        <p>Please review the above list and take appropriate action to manage the products.<br><br>
                        <p>Regards,</p>
                        <p>{self.env.user.name}</p>
                    """
			mails = {
                'subject': "Product Expiration Alert",
                'email_from': self.env.user.email,
                'email_to': inv_user_id.partner_id.email,
                'body_html': body,
                'auto_delete': False,
            }
			mail = self.env['mail.mail'].create(mails)
			mail.send()


class StockLocation(models.Model):
	_inherit = 'stock.location'


	inventory_status = fields.Boolean('Show in Inventory Status')


class StockQuant(models.Model):
	_inherit = 'stock.quant'


	expiration_date = fields.Datetime(related='lot_id.expiration_date', string='Expiration Date', store=True)

