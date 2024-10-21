# -*- coding: utf-8 -*-

import re
from odoo import models

def _refactor_name(name):
    return re.sub(r'[^a-zA-Z0-9\s]', ' ', name)
    

class AccountEdiXmlUBL20(models.AbstractModel):
    _inherit = "account.edi.xml.ubl_20"
    
    def _get_partner_party_legal_entity_vals_list(self, partner):
        res = super(AccountEdiXmlUBL20, self)._get_partner_party_legal_entity_vals_list(partner)
        for data in res:
            data['registration_name'] = _refactor_name(partner.name)
        return res
    
    def _get_partner_contact_vals(self, partner):
        res = super(AccountEdiXmlUBL20, self)._get_partner_contact_vals(partner)
        res['name'] = _refactor_name(partner.name)
        return res
    
    def _get_partner_party_vals(self, partner, role):
        res = super(AccountEdiXmlUBL20, self)._get_partner_party_vals(partner, role)
        res['party_name_vals'] = [{'name': _refactor_name(partner.display_name)}]
        return res
