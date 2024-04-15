# -*- coding: utf-8 -*-
from odoo import models


class AccountEdiXmlUBLSG(models.AbstractModel):
    _inherit = "account.edi.xml.ubl_sg"
    _description = "SG BIS Billing 3.0"

    

    def _get_partner_party_identification_vals_list(self, partner):
        """ Override to include/update values specific to ZATCA's UBL 2.1 specs """
        if partner.applicable_invoicenow :
            return [{
                'id_attrs': {'schemeID': '0035'},
                'id': partner.l10n_sg_unique_entity_number if partner.l10n_sg_unique_entity_number != 'TIN' else partner.vat
            }]
        else :
            return super()._get_partner_party_identification_vals_list(partner)
    
    def _get_country_vals(self, country):
        return {
            'country': country,
            'identification_code': country.code,
            # 'name': country.name,
        }
    
    def _get_partner_address_vals(self, partner):
        if partner.applicable_invoicenow :
            return {
                'street_name': partner.street,
                'additional_street_name': partner.street2,
                'city_name': partner.city,
                'postal_zone': partner.zip,
                'country_subentity': partner.state_id.name,
                # 'country_subentity_code': partner.state_id.code,
                'country_vals': self._get_country_vals(partner.country_id),
            }
        else : 
            return super()._get_partner_address_vals(partner=partner)
    
    def _get_partner_party_tax_scheme_vals_list(self, partner, role):
        if partner.applicable_invoicenow :
            return [{
                # 'registration_name': partner.name,
                'company_id': partner.vat,
                # 'registration_address_vals': self._get_partner_address_vals(partner),
                'TaxScheme_vals': {},
                'tax_scheme_id': 'VAT',
            }]
        else : 
            return super()._get_partner_party_tax_scheme_vals_list(partner=partner,role=role)

    
    def _export_invoice_vals(self, invoice):
        # EXTENDS account.edi.xml.ubl_bis3
        vals = super()._export_invoice_vals(invoice)
        if invoice.partner_id.applicable_invoicenow :
            commercial_partner = invoice.partner_id.commercial_partner_id

            vals['vals'].update({
                'ubl_version_id': '2.1',
                'main_template': 'invoice_now.ubl_20_Invoice_now',
                'buyer_reference' : commercial_partner.ref if commercial_partner and commercial_partner.ref else None,
                'invoice_period_vals_list' : [{
                    'start_date' : invoice.invoice_date,
                    'end_date' : invoice.invoice_date_due
                }],
                'billing_reference_vals': {
                        'id': invoice.ref if invoice.ref else invoice.name,
                        'issue_date': invoice.invoice_date,
                    }
            })
            if invoice.move_type == 'out_invoice':
                vals['main_template'] = 'invoice_now.ubl_20_Invoice_now'
            else:
                vals['main_template'] = 'invoice_now.ubl_20_CreditNote_invoicenow'

        return vals
