# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class StockPicking(models.Model):
	_inherit = 'stock.picking'

	
	@api.model
	def _get_driver_id_domain(self):
		sale_order_id = self.env['sale.order'].sudo().search([('name','=',self.origin)])
		print("\n\n self.sale id ==== ",sale_order_id,self.origin,self.name,self)
		if sale_order_id:
			partner_shipping_id = self.sale_id.partner_shipping_id if self.sale_id.partner_shipping_id else self.sale_id.partner_id
			zipcode = partner_shipping_id.zip
			delivery_code = str(zipcode[0:2]) if zipcode else False
			postal_code_id = self.env['postal.code'].search([('code','=',delivery_code)])
			self.driver_ids = self.env['res.partner'].search([('is_driver','=',True),('postal_code_ids','in',postal_code_id.ids)]) 
		
	driver_id = fields.Many2one('res.partner',string="Driver")
	forwarder_id = fields.Many2one('res.partner',string="Forwarder")
	driver_ids = fields.Many2many('res.partner',string="Driver",compute="_get_driver_id_domain")
	vehicle_id = fields.Many2one('fleet.vehicle',string="Vehicle")
	assign_driver = fields.Boolean(string="Driver Assign")
	signature_uploded = fields.Boolean(string="Signature Uploded")
	signature = fields.Image(string="Signature",copy=False, attachment=True, max_width=1024, max_height=1024)
	signed_by = fields.Char(string="Signed By", copy=False)
	signed_on = fields.Datetime(string="Signed On", copy=False)
	packing_dimentions = fields.Char(string="Packing Dimentions")


	@api.onchange('carrier_id')
	def onchange_carrier_id(self):
		for res in self:
			if res.carrier_id :
				res.forwarder_id = res.carrier_id.assigned_driver
				res.driver_id = False


	def make_picking_done(self):
		if self.state == 'assigned':
			picking_id = self
			if picking_id.state == 'draft':
				picking_id.action_assign()

			if picking_id.state in ('waiting','confirmed'):
				picking_id.action_assign()

			if picking_id.state == 'assigned':
				picking_id.with_context(cancel_backorder=False)._action_done()

			if picking_id.state in ('assigned'):
				immediate_transfer_line_ids = []
				for picking in picking_id:
					immediate_transfer_line_ids.append([0, False, {'picking_id': picking.id,'to_immediate': True,}])
				res_u = self.env['stock.immediate.transfer'].create({
						'pick_ids': [(4, p.id) for p in picking_id],
						'show_transfers': False,
						'immediate_transfer_line_ids': immediate_transfer_line_ids
						})
				res_u.with_context(button_validate_picking_ids=res_u.pick_ids.ids).process()
		return True

