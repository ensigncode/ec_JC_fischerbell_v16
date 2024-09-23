from odoo import _, api, fields, models

class RequestSaleLinePrice(models.TransientModel):
    _name = 'request.sale.line.price'
    _description = 'Request Sale Line Price'

    old_price = fields.Float('Old Price')
    requested_price = fields.Float('Request Price')

    @api.model
    def default_get(self, fields):
        res = super(RequestSaleLinePrice, self).default_get(fields)
        line_id = self.env["sale.order.line"].search([("id",'=',self._context.get("active_id"))])
        res.update({'old_price': line_id.price_unit})
        return res

    def action_request_price(self):
        context = dict(self._context or {})
        line_id = self.env["sale.order.line"].search([("id",'=',context.get("active_id"))])
        line_id.write({'request_price':self.requested_price,
                       'is_requested':True,
                       'is_request_updated':False,
                       'approval_state':'pending'})
        user_id = self.env['res.users'].sudo().search([('groups_id', 'in', self.env.ref('account.group_account_manager').id)], limit = 1)
        self.env['mail.activity'].sudo().create({
                'res_model_id': self.env.ref('sale.model_sale_order_line').id,
                'res_id': line_id.id,
                'user_id': user_id.id,
                'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                'summary': _('Price Update Requested for:%s'%line_id.order_id.name),
                'note': _('<b>Price Update Request <br/> Sale Order:</b>%s <br/> <b>Product:</b>%s <br/> <b>Old Price:</b>%s <br> <b>Requested Price:</b>%s')%(line_id.order_id.name,line_id.product_id.name,line_id.price_unit,line_id.request_price)
            })
        return True