
from odoo import _, api, fields, models

class ServiceTypeProductLine(models.Model):
    _name = 'service.type.product.line'

    picking_id = fields.Many2one('stock.picking', 'Picking')
    product_id = fields.Many2one("product.product")
    product_uom_qty = fields.Float("Demand Qty")
    product_uom = fields.Many2one("uom.uom","UoM")
    price_unit = fields.Float("Price Unit")

