
from odoo import api, fields, models

class MrpBom(models.Model):
	_inherit = 'mrp.bom'
	
	bom_type = fields.Selection([ 
        ('phantom', 'Kit'),('subcontract','Subcontracting')],string = 'BoM Type')
	
	@api.onchange('bom_type')
	def onchange_type(self):
		for res in self :
			if res.type:
				res.type = res.bom_type
