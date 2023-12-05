
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class AvaliableProductQty(models.TransientModel):
    _name = 'avaliable.product.qty'

    @api.model
    def default_get(self, fields):
        res = super(AvaliableProductQty, self).default_get(fields)
        sale_id = self.env["sale.order"].search([("id",'=',self._context.get("active_id"))])
        line_ids = sale_id.order_line.mapped(lambda line: (0, 0, {'product_id': line.product_id.id,
                            "demand_qty" : line.product_uom_qty,
                            "avaliable_qty": line.product_template_id.qty_available
                            }))
        res.update({'avaliable_product_qty_line': line_ids})
        return res

    avaliable_product_qty_line = fields.One2many("avaliable.product.qty.line","avaliable_product_qty_id",string="Avaliable")

    def action_confirm(self):
        sale_id = self.env["sale.order"].search([("id", '=', self._context.get("active_id"))])
        if sale_id.state == 'waiting_approval' and sale_id.approval_state == 'waiting_approval' and self.env.user.has_group(
                "fischerbell_custom.group_sales_order_approver"):
            sale_id.write({
                'state': 'sale',
                'approval_state': 'approved',
		'reviewed_by': self.env.user.id
            })
            sale_id.action_confirm()
            for move in sale_id.picking_ids.move_ids_without_package:
                available_product_qty_lines = self.avaliable_product_qty_line.filtered(
                    lambda ap: ap.product_id == move.product_id)
                if available_product_qty_lines:
                    line = available_product_qty_lines[0]
                    move.write({
                        'product_uom_qty': line.avaliable_qty
                    })
            for p_line in sale_id.picking_ids:
                line_ids = sale_id.order_line.filtered(lambda so_line: so_line.product_id.detailed_type == "service").mapped(lambda line: (0, 0, {'product_id': line.product_id.id,
                                                                          "product_uom_qty": line.product_uom_qty,
                                                                          "product_uom": line.product_uom.id,
                                                                          "picking_id": p_line.id,
                                                                          "price_unit": line.price_unit,
                                                                          }))
                p_line.update({'order_lines': line_ids})
        else:
            raise ValidationError("Sorry, you are not allowed to approve this order.")
        return True

class AvaliableProductQtyLine(models.TransientModel):
    _name = 'avaliable.product.qty.line'

    avaliable_product_qty_id = fields.Many2one("avaliable.product.qty.line")
    product_id = fields.Many2one("product.product")
    demand_qty = fields.Float("Demand Qty")
    avaliable_qty = fields.Float("Avaliable Qty")
