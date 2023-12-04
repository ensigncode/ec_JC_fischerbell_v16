# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json
import datetime
import math
import re

from ast import literal_eval
from collections import defaultdict
from dateutil.relativedelta import relativedelta
from datetime import datetime, date

from odoo import api, fields, models, _, Command
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_round, float_is_zero, format_datetime
from odoo.tools.misc import OrderedSet, format_date, groupby as tools_groupby

from odoo.addons.stock.models.stock_move import PROCUREMENT_PRIORITIES

SIZE_BACK_ORDER_NUMERING = 3


class MrpProduction(models.Model):
	""" Manufacturing Orders """
	_inherit = 'mrp.production'

	partner_id = fields.Many2one('res.partner', 'Partner')
	requestor_id = fields.Many2one('res.partner', 'Requestor')
	note = fields.Char('Note')
	mrp_team_id = fields.Many2one('res.users', 'MRP Team',default=lambda self: self.env.user)
	notes = fields.Html('Terms and Conditions')
	user = fields.Many2one('res.users', default=lambda self: self.env.user)
	today = fields.Datetime(string='Singapore Date & Time', default=datetime.now(), tz='Asia/Indonesia')
	delivery_date = fields.Date('Delivery Date')
	consignment_period_id = fields.Many2one('account.payment.term','Consignment Period')
	sale_id = fields.Many2one('sale.order', 'Sale Order')
	len_note = fields.Char('Length Internal Notee', compute="_compute_mrp_internal_note", store=True)
	partner_note = fields.Text('Note')
	bom_id = fields.Many2one(
        'mrp.bom', 'Bill of Material', readonly=False,
        domain="""[
        '&',
            '|',
                ('company_id', '=', False),
                ('company_id', '=', company_id),
            '&',
                '|',
                    ('product_id','=',product_id),
                    '&',
                        ('product_tmpl_id.product_variant_ids','=',product_id),
                        ('product_id','=',False),
        ('type', 'in', ['normal','phantom'])]""",
        check_company=True, compute='_compute_bom_id', store=True, precompute=True,copy=True,
        help="Bill of Materials allow you to define the list of required components to make a finished product.")


	# def action_confirm(self):
	# 	res = super(MrpProduction, self).action_confirm()
	# 	for mrp in self:
	# 		if mrp.picking_ids:
	# 			for pick in mrp.picking_ids:
	# 				pick.user = self.env.user.id

	# 		if mrp.bom_id.type == 'phantom':
	# 			picking_type = self.env['stock.picking.type'].search([
	# 				('code','=','internal'),
	# 				('sequence_code','=','SFP'),
	# 				('default_location_src_id.barcode','=','WH-POSTPRODUCTION')], limit=1)
	# 			if picking_type:
	# 				seq_date = fields.Datetime.context_timestamp(self, datetime.now())
	# 				pl_name = self.env['ir.sequence'].next_by_code('store.finished.product', sequence_date=seq_date)
	# 				picking = self.env['stock.picking'].create({
	# 						'name': pl_name,
	# 						'picking_type_id': picking_type.id, 
	# 						'origin': mrp.name,
	# 						'operation_id': mrp.id,
	# 						'sale_id': mrp.sale_id.id
	# 					})
	# 				procurement = False
	# 				procurement = self.env['procurement.group'].search([('name','=',mrp.sale_id.name)], limit=1)
	# 				if not procurement:
	# 					procurement = self.env['procurement.group'].create({'name': mrp.sale_id.name, 'move_type': 'direct'})
	# 				stock_move = self.env['stock.move'].create({
	# 						'picking_id': picking.id, 
	# 						'product_id': mrp.product_id.id,
	# 						'product_uom_qty': mrp.product_qty,
	# 						'location_id': picking.location_id.id,
	# 						'location_dest_id': picking.location_dest_id.id,
	# 						'name': picking.origin,
	# 						'group_id': procurement.id,

	# 					})
	# 				stock_move.write({'state': 'waiting'})
	# 	return res


	@api.depends('partner_note')
	def _compute_mrp_internal_note(self):
		self.len_note = False
		for inv in self:
			if inv.partner_note:
				inv.len_note = len(inv.partner_note)
			else:
				inv.len_note = False


	@api.onchange('partner_id')
	def onchange_partner_id(self):
		if self.partner_id and self.partner_id.child_ids:
			for child in self.partner_id.child_ids:
				if child.type == 'contact':
					self.requestor_id = child
				else:
					self.requestor_id = False
		else:
			self.requestor_id = False

		for order in self:
			if order.partner_id:
				if order.partner_id.parent_id:
					config_note = self.env['fischerbell.configuration.note'].search([
				        ('type', '=', 'manufacture'),
				        ('partner_ids', 'in', [order.partner_id.parent_id.id])  # Use a list to compare with a Many2many field
				    ], limit=1)
					order.partner_note = config_note.note
				else:
					config_note = self.env['fischerbell.configuration.note'].search([
				        ('type', '=', 'manufacture'),
				        ('partner_ids', 'in', [order.partner_id.id])  # Use a list to compare with a Many2many field
				    ], limit=1)
					order.partner_note = config_note.note



	def action_consignment_send(self):
		self.ensure_one()
		ir_model_data = self.env['ir.model.data']
		try:
			if self.env.context.get('is_consignment_send', True):
				template_id = ir_model_data._xmlid_lookup('fischerbell_custom.fischerbell_consignment_note_template_email')[2]
			else:
				template_id = False
		except ValueError:
			template_id = False
		try:
			compose_form_id = ir_model_data._xmlid_lookup('mail.email_compose_message_wizard_form')[2]
		except ValueError:
			compose_form_id = False
		ctx = dict(self.env.context or {})
		ctx.update({
			'default_model': 'mrp.production',
			'active_model': 'mrp.production',
			'active_id': self.ids[0],
			'default_res_id': self.ids[0],
			'default_use_template': bool(template_id),
			'default_template_id': template_id,
			'default_composition_mode': 'comment',
			'default_email_layout_xmlid': "mail.mail_notification_layout_with_responsible_signature",
			'force_email': True,
			'is_consignment_send': True
		})

		# In the case of a RFQ or a PO, we want the "View..." button in line with the state of the
		# object. Therefore, we pass the model description in the context, in the language in which
		# the template is rendered.
		lang = self.env.context.get('lang')
		if {'default_template_id', 'default_model', 'default_res_id'} <= ctx.keys():
			template = self.env['mail.template'].browse(ctx['default_template_id'])
			if template and template.lang:
				lang = template._render_lang([ctx['default_res_id']])[ctx['default_res_id']]

		self = self.with_context(lang=lang)
		ctx['model_description'] = _('Consignment Note')

		return {
			'name': _('Compose Email'),
			'type': 'ir.actions.act_window',
			'view_mode': 'form',
			'res_model': 'mail.compose.message',
			'views': [(compose_form_id, 'form')],
			'view_id': compose_form_id,
			'target': 'new',
			'context': ctx,
		}
	# 	""" Opens a wizard to compose an email, with relevant mail template loaded by default """
	# 	self.ensure_one()
	# 	lang = self.env.context.get('lang')
	# 	mail_template = self._find_mail_template()
	# 	if mail_template and mail_template.lang:
	# 		lang = mail_template._render_lang(self.ids)[self.id]
	# 	ctx = {
	# 		'default_model': 'mrp.production',
	# 		'default_res_id': self.id,
	# 		'default_use_template': bool(mail_template),
	# 		'default_template_id': mail_template.id if mail_template else None,
	# 		'default_composition_mode': 'comment',
	# 		'is_consignment_send': True,
	# 		'default_email_layout_xmlid': 'mail.mail_notification_layout_with_responsible_signature',
	# 		'force_email': True,
	# 	}
	# 	return {
	# 		'type': 'ir.actions.act_window',
	# 		'view_mode': 'form',
	# 		'res_model': 'mail.compose.message',
	# 		'views': [(False, 'form')],
	# 		'view_id': False,
	# 		'target': 'new',
	# 		'context': ctx,
	# 	}


	# def _find_mail_template(self):
	# 	""" Get the appropriate mail template for the current sales order based on its state.

	# 	If the SO is confirmed, we return the mail template for the sale confirmation.
	# 	Otherwise, we return the quotation email template.

	# 	:return: The correct mail template based on the current status
	# 	:rtype: record of `mail.template` or `None` if not found
	# 	"""
	# 	self.ensure_one()
	# 	mail_template = False
	# 	if self.env.context.get('is_consignment_send') == True:
	# 		return self.env.ref('fischerbell_custom.fischerbell_consignment_note_template_email', raise_if_not_found=False)
	# 	else:
	# 		return mail_template