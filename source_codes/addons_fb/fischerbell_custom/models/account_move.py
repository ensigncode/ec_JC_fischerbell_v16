# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api,fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import calendar

class AccountMove(models.Model):
	_inherit = "account.move"

	purchase_order_id = fields.Many2one('purchase.order', 'Purchase Order')
	move_ids = fields.One2many('account.move','account_move_id','Freight Charge')
	account_move_id = fields.Many2one('account.move','Bill')
	move_count = fields.Integer('Move Count', compute="_compute_move_ids")
	is_freight_charge = fields.Boolean('Is Freight Charge Bill', default=False)
	sale_id = fields.Many2one('sale.order', 'Sale Order')
	current_month = fields.Monetary('Current Month', compute="_compute_outstanding_amount", store=True)
	over_1month = fields.Monetary('Current Month', store=True, compute="_compute_outstanding_amount")
	over_2month = fields.Monetary('Current Month', store=True, compute="_compute_outstanding_amount")
	over_3month = fields.Monetary('Current Month', store=True, compute="_compute_outstanding_amount")
	over_4month = fields.Monetary('Current Month', store=True, compute="_compute_outstanding_amount")
	total_balance_due = fields.Monetary('Balance Due')
	user = fields.Many2one('res.users', default=lambda self: self.env.user)
	today = fields.Datetime('Date and Time', default=datetime.now())
	amount_undiscounted = fields.Float(
		string="Amount Before Discount",
		compute='_compute_amount_undiscounted', digits=0)
	internal_note = fields.Char('')
	len_note = fields.Char('Length Internal Notee', compute="_compute_internal_note", store=True)
	partner_note = fields.Text('Note')
	delivery_instruction = fields.Html(string="Delivery Instruction")
	invoice_instruction = fields.Html(string="Invoice Instruction")

	    

	@api.depends('posted_before', 'state', 'journal_id', 'date')
	def _compute_name(self):
		super(AccountMove, self)._compute_name()
		credit_note, debit_note, journal_entry, cash_entry= (["CN"], ["DN"], ["JE"], ["PC"])
		# name_get = self.name.split('/')[::-2]
		for rec in self:
			if rec.name:
				name_get = rec.name.split('/')
				name_get.pop(0)
			if self._context.get('default_move_type') == 'out_refund':
				new_name = credit_note + name_get
				if new_name[1]:
					nm = '/'.join(new_name)
					rec.name = nm
			if self._context.get('default_move_type') == 'in_refund':
				new_name = debit_note + name_get
				if new_name[1]:
					if len(new_name) > 3:
						new_name.pop(-2)
						nm = '/'.join(new_name)
						rec.name = nm
					else:
						nm = '/'.join(new_name)
						rec.name = nm
			if self._context.get('default_move_type') == 'entry':
				new_name = journal_entry + name_get
				if new_name[1]:
					nm = '/'.join(new_name)
					rec.name = nm
			if self._context.get('default_move_type') == 'entry' and rec.journal_id.type == 'cash':
				new_name = cash_entry + name_get
				if new_name[1]:
					nm = '/'.join(new_name)
					rec.name = nm
		return True

	# credit_note, debit_note, journal_entry = ["CN"], ["DN"], ["JE"]
	#
	# if self.name and 'default_move_type' in self._context:
	# 	name_get = self.name.split('/')[1:]
	# 	move_type = self._context['default_move_type']
	#
	# 	if move_type == 'out_refund':
	# 		self.name = '/'.join(credit_note + name_get[1:]) if name_get[1] else self.name
	#
	# 	elif move_type == 'in_refund':
	# 		self.name = '/'.join(debit_note + name_get[1:-1]) if name_get[1] and len(name_get) > 3 else '/'.join(
	# 			debit_note + name_get[1:])
	#
	# 	elif move_type == 'entry':
	# 		self.name = '/'.join(journal_entry + name_get[1:]) if name_get[1] else self.name

	@api.onchange('partner_id')
	def _inverse_partner_id(self):
		super()._inverse_partner_id()
		for order in self:
			if order.partner_id:
				config_note = self.env['fischerbell.configuration.note'].search([
					('type', '=', 'account'),
					('partner_ids', 'in', [order.partner_id.id])  # Use a list to compare with a Many2many field
				], limit=1)
				order.partner_note = config_note.note

	@api.depends('partner_note')
	def _compute_internal_note(self):
		self.len_note = False
		for inv in self:
			if inv.partner_note:
				inv.len_note = len(inv.partner_note)
			else:
				inv.len_note = False

	def _compute_amount_undiscounted(self):
		for order in self:
			total = 0.0
			for line in order.invoice_line_ids:
				total += (line.price_subtotal * 100)/(100-line.discount) if line.discount != 100 else (line.price_unit * line.quantity)
			order.amount_undiscounted = total


	@api.depends('state','payment_state')
	def _compute_outstanding_amount(self):
		self.current_month = False
		self.over_1month = False
		self.over_2month = False
		self.over_3month = False
		self.over_4month = False
		month = False
		over_1month = False
		over_2month = False
		over_3month = False
		over_4month = False
		outstanding_amount = 0
		outstanding_amount1 = 0
		outstanding_amount2 = 0
		outstanding_amount3 = 0
		outstanding_amount4 = 0
		invoices = False
		for inv in self:
			if inv.state == 'posted' and inv.payment_state not in ['in_payment','paid']:
				date_current = inv.invoice_date_due
				month_current = datetime.strftime(date_current,'%m')
				year_current = datetime.strftime(date_current,'%Y')
				data = calendar.monthrange(int(year_current),int(month_current))
				datestart = datetime.strptime(year_current+'-'+month_current+'-01','%Y-%m-%d')
				enddate = datetime.strptime(year_current+'-'+month_current+'-'+"%02d" % (data[1]),'%Y-%m-%d')

				domain = [
						('account_id', '=', self.env.ref('l10n_generic_coa.1_receivable').id),
						('move_id.state', '=', 'posted'),
						('partner_id', '=', inv.partner_id.id),
						('reconciled', '=', False),
						('balance', '<', 0.0),
						'|', ('amount_residual', '!=', 0.0), ('amount_residual_currency', '!=', 0.0),
					]
				for line in self.env['account.move.line'].search(domain):
					date = line.move_id.date.strftime('%m')

					#Current Month
					inv_month = month_current

					# Current 1 Month
					current_1month = int(month_current) - 1
					if len(str(current_1month)) == 1:
						over_1month = str(current_1month).zfill(2)
					else:
						over_1month = current_1month


					# Current 2 Month
					current_2month = int(month_current) - 2
					if len(str(current_2month)) == 1:
						over_2month = str(current_2month).zfill(2)
					else:
						over_2month = current_2month


					# Current 3 Month
					current_3month = int(month_current) - 3
					if len(str(current_3month)) == 1:
						over_3month = str(current_3month).zfill(2)
					else:
						over_3month = current_3month


					# Current 4 Month
					current_4month = int(month_current) - 4
					if len(str(current_4month)) == 1:
						over_4month = str(current_4month).zfill(2)
					else:
						over_4month = current_4month

					if line.date and line.date.strftime('%m') == inv_month:
						outstanding_amount += line.amount_residual_currency

					if line.date and line.date.strftime('%m') == over_1month:
						outstanding_amount1 += line.amount_residual_currency

					if line.date and line.date.strftime('%m') == over_2month:
						outstanding_amount2 += line.amount_residual_currency

					if line.date and line.date.strftime('%m') == over_3month:
						outstanding_amount3 += line.amount_residual_currency

					if line.date and line.date.strftime('%m') == over_4month:
						outstanding_amount4 += line.amount_residual_currency

			invoices = self.env['account.move'].search([('partner_id','=',inv.partner_id.id)])

		if invoices:
			for invoice in invoices:
				invoice.current_month = abs(outstanding_amount)
				invoice.over_1month = abs(outstanding_amount + outstanding_amount1)
				invoice.over_2month = abs(outstanding_amount + outstanding_amount1 + outstanding_amount2)
				invoice.over_3month = abs(outstanding_amount + outstanding_amount1 + outstanding_amount2 + outstanding_amount3)
				invoice.over_4month = abs(outstanding_amount + outstanding_amount1 + outstanding_amount2 + outstanding_amount3 + outstanding_amount4)



	def create_freight_charge(self):
		product_id = int(self.env['ir.config_parameter'].sudo().get_param('fischerbell_custom.freight_charge_id'))
		for bill in self:
			bill_state = bill.move_ids.filtered(lambda x: x.state not in 'cancel')
			if bill.move_ids and bill_state:
				raise UserError("The vendor bills already have the freight charges. Please cancel the first freight charge bill to create a new one.")
			
			if product_id:
				move = bill.copy()
				move.write({'account_move_id': bill.id, 'is_freight_charge': True, 'ref': bill.name})
				move.update({'invoice_line_ids': False})
				move.update({'invoice_line_ids': [(0,0,{'product_id': product_id})]})
			else:
				raise UserError("There is no product for Freight Charge. Please check your configuration.")

		return


	def action_view_freight_charge(self):
		self.ensure_one()
		return {
			'type': 'ir.actions.act_window',
			'name': 'Freight Charges',
			'view_mode': 'tree,form',
			'res_model': 'account.move',
			'domain': [('account_move_id', '=', self.id),('move_type','=','in_invoice'),('is_freight_charge','=',True)],
			'context': {'move_type': 'in_invoice', 'form_view_ref': 'account.view_move_form', 'tree_view_ref':'account.view_in_invoice_bill_tree'}
		}


	@api.depends('move_ids')
	def _compute_move_ids(self):
		for bill in self:
			move_ids = list(filter(lambda x: (x.move_type == 'in_invoice' and x.account_move_id == bill.id and x.is_freight_charge == True, x.ref == bill.name), bill.move_ids))
			bill.move_count = len(move_ids)


	def _get_name_invoice_report(self):
		""" This method need to be inherit by the localizations if they want to print a custom invoice report instead of
		the default one. For example please review the l10n_ar module """
		self.ensure_one()
		return 'fischerbell_custom.fischerbell_report_invoice_document'

	def action_invoice_sent(self):
		""" Open a window to compose an email, with the edi invoice template
            message loaded by default
        """
		self.ensure_one()
		template = self.env.ref(self._get_mail_template(), raise_if_not_found=False)
		lang = False
		if template:
			lang = template._render_lang(self.ids)[self.id]
		if self.env.ref('account.email_template_edi_invoice').id == template.id:
			template.email_to = self.partner_id.parent_id.e_invoice_email if self.partner_id.parent_id else self.partner_id.e_invoice_email
		if not lang:
			lang = get_lang(self.env).code
		compose_form = self.env.ref('account.account_invoice_send_wizard_form', raise_if_not_found=False)
		ctx = dict(
			default_model='account.move',
			default_res_id=self.id,
			# For the sake of consistency we need a default_res_model if
			# default_res_id is set. Not renaming default_model as it can
			# create many side-effects.
			default_res_model='account.move',
			default_use_template=bool(template),
			default_template_id=template and template.id or False,
			default_composition_mode='comment',
			mark_invoice_as_sent=True,
			default_email_layout_xmlid="mail.mail_notification_layout_with_responsible_signature",
			model_description=self.with_context(lang=lang).type_name,
			force_email=True,
			active_ids=self.ids,
		)
		report_action = {
			'name': _('Send Invoice'),
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'account.invoice.send',
			'views': [(compose_form.id, 'form')],
			'view_id': compose_form.id,
			'target': 'new',
			'context': ctx,
		}

		if self.env.is_admin() and not self.env.company.external_report_layout_id and not self.env.context.get(
				'discard_logo_check'):
			return self.env['ir.actions.report']._action_configure_external_report_layout(report_action)

		return report_action


