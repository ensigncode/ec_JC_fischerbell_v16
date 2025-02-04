# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class SaleOrder(models.Model):
	_inherit = 'sale.order'

	collection = fields.Selection([('self_collection','Send Driver For Self Collection'),('assigned_driver','Delivery')],string="Delivery Mode",default="self_collection")
	# Function will assign Vehicle And Driver in Transfer
	def assign_driver(self):
		driver_ids = False
		partner_shipping_id = self.partner_shipping_id if self.partner_shipping_id else self.partner_id
		zipcode = partner_shipping_id.zip
		delivery_code = str(zipcode[0:2]) if zipcode else False
		postal_code_id = self.env['postal.code'].search([('code','=',delivery_code)])
		purchase_order_ids = self._get_purchase_orders().ids
		if postal_code_id:
			partner_ids = self.env['res.partner'].search([('is_driver','=',True),('postal_code_ids','in',postal_code_id.ids)])
			if partner_ids:
				driver_ids = partner_ids
		return driver_ids

	def action_confirm(self):
		res = super(SaleOrder,self).action_confirm()
		if self.collection == "assigned_driver":
			driver_ids = self.assign_driver()
			if self.picking_ids and driver_ids:
				for picking in self.picking_ids:
					if not picking.carrier_id :
						picking.driver_ids = [(6,0,driver_ids.ids)]
						if driver_ids and driver_ids[0].fleet_vehicle_ids:
							picking.vehicle_id = driver_ids[0].fleet_vehicle_ids[0].id
						if len(driver_ids.ids) == 1:
							picking.driver_id = driver_ids[0].id
						if len(driver_ids.ids) > 1 :
							picking.driver_id = False
		return res

		