from odoo import models, fields, api, _

class PartnerDetails(models.TransientModel):
    _name = 'request.partner.details'
    _description = 'Request Partner Details'

    change_fields = fields.Selection([('credit_limit','Credit Limit'),('price_list','Pricelist'),
                                      ('payment_term','Payment Term'),('all','All')],string="Request Fields", default="all")
    pricelist_id = fields.Many2one('product.pricelist',string="Current PriceList", readonly="1")
    update_pricelist_id = fields.Many2one('product.pricelist',string="Request PriceList")

    payment_term_id = fields.Many2one('account.payment.term',string="Current Payment Term", readonly="1")
    update_payment_term_id = fields.Many2one('account.payment.term',string="Request Payment Term")

    credit_limit = fields.Float(string="Current Credit Limit", readonly="1")
    update_credit_limit = fields.Float(string="Request Credit Limt")

    is_person = fields.Boolean('Is Person')

    @api.model
    def default_get(self, fields):
        res = super(PartnerDetails, self).default_get(fields)
        partner_id = self.env["res.partner"].search([("id",'=',self._context.get("active_id"))])
        res.update({'pricelist_id': partner_id.property_product_pricelist and partner_id.property_product_pricelist.id or False,
            'credit_limit': partner_id.credit_limit or 0.0,
            'payment_term_id': partner_id.property_payment_term_id and partner_id.property_payment_term_id.id or False,
            'is_person': True if partner_id.company_type == 'person' else False})
        return res

    def action_update_request(self):
        context = dict(self._context or {})
        partner_id = self.env["res.partner"].search([("id",'=',context.get("active_id"))])
        if self.change_fields == 'credit_limit':
            partner_id.write({'requested_credit_limit':self.update_credit_limit,
                'is_request_creditlimit':True,
                'creditlimit_approval_state':'pending'})
            msg = _('<b>Partner Update Request <br/> Parnter:</b>%s <br/><br/>   <b>Old Credit Limit:</b>%s <br> <b>Requested Credit Limit:</b>%s')%(partner_id.name,partner_id.credit_limit,self.update_credit_limit)
        elif self.change_fields == 'price_list':
            partner_id.write({'requested_pricelist_id':self.update_pricelist_id,
                'is_request_pricelist':True,
                'pricelist_approval_state':'pending'})
            msg = _('<b>Partner Update Request <br/> Parnter:</b>%s <br/> <br/>  <b>Old Price List:</b>%s <br/> <b>Requested Price List:</b>%s')%(partner_id.name,partner_id.property_product_pricelist and partner_id.property_product_pricelist.name or '',self.update_pricelist_id.name)
        elif self.change_fields == 'payment_term':
            partner_id.write({'requested_payment_term_id':self.update_payment_term_id,
                'is_request_paymentterm':True,
                'paymentterm_approval_state':'pending'})
            msg = _('<b>Partner Update Request <br/> Parnter:</b>%s <br/> <br/>  <b>Old Payment Term:</b>%s <br> <b>Requested Payment Term:</b>%s')%(partner_id.name,partner_id.property_payment_term_id and partner_id.property_payment_term_id.name or '',self.update_payment_term_id.name)
        else:
            partner_id.write({'requested_credit_limit':self.update_credit_limit,
                'requested_pricelist_id':self.update_pricelist_id,
                'requested_payment_term_id':self.update_payment_term_id,
                'is_request_pricelist':True,
                'pricelist_approval_state':'pending',
                'is_request_paymentterm':True,
                'paymentterm_approval_state':'pending',
                'is_request_creditlimit':True,
                'creditlimit_approval_state':'pending'})
            msg = _('<b>Partner Update Request <br/> Parnter:</b>%s <br/><br/>   <b>Old Credit Limit:</b>%s <br> <b>Requested Credit Limit:</b>%s <br/><br/>' \
                       + '<b>Old Payment Term:</b>%s <br> <b>Requested Payment Term:</b>%s <br/><br/> ' \
                       )%(partner_id.name,partner_id.credit_limit,self.update_credit_limit,
                        partner_id.property_payment_term_id and partner_id.property_payment_term_id.name or '',self.update_payment_term_id.name)
            if self.update_pricelist_id:
                msg += _('<b>Old Price List:</b>%s <br> <b>Requested Price List:</b>%s')%(partner_id.property_product_pricelist and partner_id.property_product_pricelist.name or '',self.update_pricelist_id.name)
        user_id = self.env['res.users'].sudo().search([('groups_id', 'in', self.env.ref('account.group_account_manager').id)], limit = 1)
        self.env['mail.activity'].sudo().create({
                'res_model_id': self.env.ref('base.model_res_partner').id,
                'res_id': partner_id.id,
                'user_id': user_id.id,
                'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                'summary': _('Partner Update Requested for:%s'%partner_id.name),
                'note': msg
            })
        return True