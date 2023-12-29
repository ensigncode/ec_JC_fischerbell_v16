from odoo import models, fields,api


class MailComposerMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    @api.onchange('template_id')
    def _onchange_template_id_wrapper(self):
        self.ensure_one()
        atrwork = self.env['purchase.order'].browse(self._context.get("active_id"))
        if self._context.get("active_model") == 'purchase.order' and atrwork.artwork_attachment_ids:
            values = self._onchange_template_id(self.template_id.id, self.composition_mode, self.model, self.res_id)[
                'value']
            if values.get('attachment_ids'):
                values.get('attachment_ids')[0][2].extend(atrwork.artwork_attachment_ids.ids)
            for fname, value in values.items():
                setattr(self, fname, value)
        else:
            super(MailComposerMessage, self)._onchange_template_id_wrapper()

