# -*- coding: utf-8 -*-

from odoo import models
from odoo.addons.sale_stock_renting.models.sale_order_line import RentalOrderLine


# sale_stock_renting/models/sale_order_line.py#L262
def _action_launch_stock_rule(self, previous_product_uom_qty=False):
    """Disable stock moves for rental order lines.

    Stock moves for rental orders are created on pickup/return.
    The rental reservations are not propagated in the stock until
    the effective pickup or returns.
    """
    # Commented below lines to create picking
    # other_lines = self.filtered(lambda sol: not sol.is_rental)
    super(RentalOrderLine, self)._action_launch_stock_rule(previous_product_uom_qty)

RentalOrderLine._action_launch_stock_rule = _action_launch_stock_rule
