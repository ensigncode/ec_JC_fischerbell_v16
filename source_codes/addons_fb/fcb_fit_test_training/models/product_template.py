# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, models, tools, _, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_fit_test_training = fields.Boolean(string="Is Fit Test Training")