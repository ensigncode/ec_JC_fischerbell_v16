# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, Command


class FollowupManualReminder(models.TransientModel):
    _inherit = 'account_followup.manual_reminder'

    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        assert self.env.context['active_model'] == 'res.partner'
        partner = self.env['res.partner'].browse(self.env.context['active_ids'])
        partner.ensure_one()
        followup_line = partner.followup_line_id
        if followup_line:
            defaults.update(
                email=followup_line.send_email,
                sms=followup_line.send_sms,
                template_id=followup_line.mail_template_id.id,
                sms_template_id=followup_line.sms_template_id.id,
                join_invoices=followup_line.join_invoices,
                email_to=partner.parent_id.soa_email if partner.parent_id else partner.soa_email ,
            )
        defaults.update(
            partner_id=partner.id,
            email_recipient_ids=[Command.set((partner._get_all_followup_contacts() or partner).ids)],
            attachment_ids=[Command.set(partner._get_included_unreconciled_aml_ids().move_id.message_main_attachment_id.ids)],
        )
        return defaults

    email_to = fields.Char("Email To")


    @api.onchange('email')
    def _onchange_email(self):
        partner = self.env['res.partner'].browse(self.env.context['active_ids'])
        for rec in self:
            if rec.email == True:
                rec.email_to=partner.parent_id.soa_email if partner.parent_id else partner.soa_email


    def _get_wizard_options(self):
        """ Returns a dictionary of options, containing values from this wizard that are needed to process the followup
        """
        return {
            'partner_id': self.partner_id,
            'email': self.email,
            'email_subject': self.subject,
            'email_recipient_ids': self.email_recipient_ids,
            'body': self.body_html,
            'attachment_ids': self.attachment_ids.ids,
            'sms': self.sms,
            'sms_body': self.sms_body,
            'print': self.print,
            'join_invoices': self.join_invoices,
            'manual_followup': True,
            'email_to':self.email_to,
        }
