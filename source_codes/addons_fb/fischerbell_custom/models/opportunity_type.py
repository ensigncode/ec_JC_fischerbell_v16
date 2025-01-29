
from odoo import _, api, fields, models

class OpportunityType(models.Model):
    _name = 'opportunity.type'

    name = fields.Char("Name")
