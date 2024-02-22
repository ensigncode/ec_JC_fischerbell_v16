# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class AssignDriverLine(models.TransientModel):
	_name = 'assign.driver.line'
	_description = "Assign Driver Line"

	assign_driver_ids = fields.One2many('assign.driver','assign_line_id')

	@api.model
	def default_get(self,vals):
		res = super(AssignDriverLine,self).default_get(vals)
		active_ids = self._context.get('active_ids')
		order_ids = self.env['sale.order'].browse(active_ids)
		confirmed_order_ids  = order_ids.filtered(lambda x:x.state == 'sale')
		assign_drivers = []
		for order in confirmed_order_ids:
			if order.collection == "assigned_driver":
				picking_ids = order.picking_ids.filtered(lambda x:x.state != 'done')
				if picking_ids:
					driver_ids = order.assign_driver()
					assign_drivers.append((0,0,{'order_id':order.id,
										'picking_id':picking_ids[0].id,
										'driver_ids':[(6,0,driver_ids.ids)] if driver_ids else [(6,0,[])],
										'driver_id':driver_ids[0].id if driver_ids else False,
									}))
					res['assign_driver_ids'] = assign_drivers
		return res

	def assign_driver(self):
		for line in self.assign_driver_ids:
			if line.driver_ids:
				line.picking_id.driver_ids = [(6,0,line.driver_ids.ids)]
			if line.driver_id:
				line.picking_id.driver_id = line.driver_id.id
			if line.vehicle_id:
				line.picking_id.vehicle_id = line.vehicle_id.id
		return True

class AssignDriver(models.TransientModel):
	_name = 'assign.driver'
	_description = "Assign Driver"

	driver_id = fields.Many2one('res.partner',string="Driver")
	driver_ids = fields.Many2many('res.partner',string="Drivers")
	order_id = fields.Many2one('sale.order',string="Order")
	picking_id = fields.Many2one('stock.picking',string="Transfer")
	assign_line_id = fields.Many2one('assign.driver.line',string="Assign Line")
	vehicle_id = fields.Many2one('fleet.vehicle',string="Vehicle")

	# @api.model
	# def default_get(self,vals):
	# 	res = super(AssignDriver,self).default_get(vals)
	# 	active_ids = self._context.get('active_ids')
	# 	order_id = self.env['sale.order'].browse(active_ids)
	# 	customer_ids = order_id.mapped('partner_id')
	# 	customer = False
	# 	for order in order_id:
	# 		if customer == False:
	# 			customer = order.partner_id.id
	# 			for picking in order.picking_ids.filtered(lambda x:x.state =='done' ):
	# 				if picking.assign_driver == False or picking.assign_driver == True:
	# 					postal_two_digit = str(picking.partner_id.zip)[:2]
	# 					postal_ids = self.env['postal.code'].search([('code','=',postal_two_digit)])
	# 					partner_ids = self.env['res.partner'].search([('postal_code_ids','in',postal_ids.ids)])
	# 					if partner_ids:
	# 						res.update({'driver_ids':[(6,0,partner_ids.ids)]})
	# 		if customer != order.partner_id.id:
	# 			raise UserError(_("All selected sale orders must belong to different customers."))
	# 	return res


	# def delivery_driver_assign(self):
	# 	active_ids = self._context.get('active_ids')
	# 	order_id = self.env['sale.order'].browse(active_ids)
	# 	for picking in order_id.picking_ids.filtered(lambda x:x.state =='done' and x.assign_driver == False):
	# 		picking.driver_id = self.driver_id
	# 		picking.driver_ids = [(6,0,self.driver_ids.ids)]
	# 		picking.assign_driver = True
