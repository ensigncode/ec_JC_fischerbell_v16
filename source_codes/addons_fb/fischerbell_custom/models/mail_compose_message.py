from odoo import models, fields,api, Command, registry, SUPERUSER_ID, _
import base64
import logging
from odoo.tools.misc import clean_context, split_every
import threading

_logger = logging.getLogger(__name__)


class Message(models.Model):
    _inherit = 'mail.message'
    
    email_cc = fields.Char('Email Cc')

    @api.model
    def open_unread_messages(self):
        """Get unread message IDs for the current user."""
        # Find all mail channel members for the current user
        members = self.env['mail.channel.member'].search([
            ('partner_id', '=', self.env.user.partner_id.id)
        ])

        if not members:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'mail.message',
                'view_mode': 'tree,form',
                'domain': [],
            }

        member_ids = tuple(members.ids)

        # Fetch unread messages based on the member IDs
        self.env.cr.execute("""
               SELECT mail_message.id
               FROM mail_message
               INNER JOIN mail_channel_member
                   ON mail_channel_member.channel_id = mail_message.res_id
               WHERE mail_message.model = 'mail.channel'
                 AND mail_message.message_type NOT IN ('notification', 'user_notification')
                 AND (
                     mail_message.id > mail_channel_member.seen_message_id
                     OR mail_channel_member.seen_message_id IS NULL
                 )
                 AND mail_channel_member.id IN %s
           """, (member_ids,))

        unread_message_ids = [item[0] for item in self.env.cr.fetchall()]

        # Return action with the domain for unread messages
        return {
            'name': _('Unread Message'),
            'type': 'ir.actions.act_window',
            'res_model': 'mail.message',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', unread_message_ids)],
        }
    
    
class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'
    
    def _notify_thread_by_email(self, message, recipients_data, msg_vals=False,
                                mail_auto_delete=True,  # mail.mail
                                model_description=False, force_email_company=False, force_email_lang=False,  # rendering
                                resend_existing=False, force_send=True, send_after_commit=True,  # email send
                                subtitles=None, **kwargs):
        """ Method to send email linked to notified messages.

        :param message: ``mail.message`` record to notify;
        :param recipients_data: list of recipients information (based on res.partner
          records), formatted like
            [{'active': partner.active;
              'id': id of the res.partner being recipient to notify;
              'groups': res.group IDs if linked to a user;
              'notif': 'inbox', 'email', 'sms' (SMS App);
              'share': partner.partner_share;
              'type': 'customer', 'portal', 'user;'
             }, {...}].
          See ``MailThread._notify_get_recipients``;
        :param msg_vals: dictionary of values used to create the message. If given it
          may be used to access values related to ``message`` without accessing it
          directly. It lessens query count in some optimized use cases by avoiding
          access message content in db;

        :param mail_auto_delete: delete notification emails once sent;

        :param model_description: model description used in email notification process
          (computed if not given);
        :param force_email_company: see ``_notify_by_email_prepare_rendering_context``;
        :param force_email_lang: see ``_notify_by_email_prepare_rendering_context``;

        :param resend_existing: check for existing notifications to update based on
          mailed recipient, otherwise create new notifications;
        :param force_send: send emails directly instead of using queue;
        :param send_after_commit: if force_send, tells whether to send emails after
          the transaction has been committed using a post-commit hook;
        :param subtitles: optional list that will be set as template value "subtitles"
        """
        partners_data = [r for r in recipients_data if r['notif'] == 'email']
        if not partners_data:
            return True

        model = msg_vals.get('model') if msg_vals else message.model
        model_name = model_description or (self.env['ir.model']._get(model).display_name if model else False) # one query for display name
        recipients_groups_data = self._notify_get_recipients_classify(partners_data, model_name, msg_vals=msg_vals)

        if not recipients_groups_data:
            return True
        force_send = self.env.context.get('mail_notify_force_send', force_send)

        template_values = self._notify_by_email_prepare_rendering_context(
            message, msg_vals=msg_vals, model_description=model_description,
            force_email_company=force_email_company,
            force_email_lang=force_email_lang,
        ) # 10 queries
        if subtitles:
            template_values['subtitles'] = subtitles

        email_layout_xmlid = msg_vals.get('email_layout_xmlid') if msg_vals else message.email_layout_xmlid
        template_xmlid = email_layout_xmlid if email_layout_xmlid else 'mail.mail_notification_layout'
        base_mail_values = self._notify_by_email_get_base_mail_values(message, additional_values={'auto_delete': mail_auto_delete})

        # Clean the context to get rid of residual default_* keys that could cause issues during
        # the mail.mail creation.
        # Example: 'default_state' would refer to the default state of a previously created record
        # from another model that in turns triggers an assignation notification that ends up here.
        # This will lead to a traceback when trying to create a mail.mail with this state value that
        # doesn't exist.
        SafeMail = self.env['mail.mail'].sudo().with_context(clean_context(self._context))
        SafeNotification = self.env['mail.notification'].sudo().with_context(clean_context(self._context))
        emails = self.env['mail.mail'].sudo()

        # loop on groups (customer, portal, user,  ... + model specific like group_sale_salesman)
        notif_create_values = []
        recipients_max = 50
        for recipients_group_data in recipients_groups_data:
            # generate notification email content
            recipients_ids = recipients_group_data.pop('recipients')
            render_values = {**template_values, **recipients_group_data}
            # {company, is_discussion, lang, message, model_description, record, record_name, signature, subtype, tracking_values, website_url}
            # {actions, button_access, has_button_access, recipients}

            mail_body = self.env['ir.qweb']._render(template_xmlid, render_values, minimal_qcontext=True, raise_if_not_found=False, lang=template_values['lang'])
            if not mail_body:
                _logger.warning('QWeb template %s not found or is empty when sending notification emails. Sending without layouting.', template_xmlid)
                mail_body = message.body
            mail_body = self.env['mail.render.mixin']._replace_local_links(mail_body)

            # create email
            for recipients_ids_chunk in split_every(recipients_max, recipients_ids):
                mail_values = self._notify_by_email_get_final_mail_values(
                    recipients_ids_chunk,
                    base_mail_values,
                    additional_values={'body_html': mail_body}
                )
                mail_values['email_cc'] = msg_vals.get('email_cc', '')
                new_email = SafeMail.create(mail_values)

                if new_email and recipients_ids_chunk:
                    tocreate_recipient_ids = list(recipients_ids_chunk)
                    if resend_existing:
                        existing_notifications = self.env['mail.notification'].sudo().search([
                            ('mail_message_id', '=', message.id),
                            ('notification_type', '=', 'email'),
                            ('res_partner_id', 'in', tocreate_recipient_ids)
                        ])
                        if existing_notifications:
                            tocreate_recipient_ids = [rid for rid in recipients_ids_chunk if rid not in existing_notifications.mapped('res_partner_id.id')]
                            existing_notifications.write({
                                'notification_status': 'ready',
                                'mail_mail_id': new_email.id,
                            })
                    notif_create_values += [{
                        'author_id': message.author_id.id,
                        'mail_message_id': message.id,
                        'res_partner_id': recipient_id,
                        'notification_type': 'email',
                        'mail_mail_id': new_email.id,
                        'is_read': True,  # discard Inbox notification
                        'notification_status': 'ready',
                    } for recipient_id in tocreate_recipient_ids]
                emails += new_email

        if notif_create_values:
            SafeNotification.create(notif_create_values)

        # NOTE:
        #   1. for more than 50 followers, use the queue system
        #   2. do not send emails immediately if the registry is not loaded,
        #      to prevent sending email during a simple update of the database
        #      using the command-line.
        test_mode = getattr(threading.current_thread(), 'testing', False)
        if force_send and len(emails) < recipients_max and (not self.pool._init or test_mode):
            # unless asked specifically, send emails after the transaction to
            # avoid side effects due to emails being sent while the transaction fails
            if not test_mode and send_after_commit:
                email_ids = emails.ids
                dbname = self.env.cr.dbname
                _context = self._context

                @self.env.cr.postcommit.add
                def send_notifications():
                    db_registry = registry(dbname)
                    with db_registry.cursor() as cr:
                        env = api.Environment(cr, SUPERUSER_ID, _context)
                        env['mail.mail'].browse(email_ids).send()
            else:
                emails.send()

        return True



class MailComposerMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    email_cc = fields.Char('Email Cc')

    @api.onchange('model')
    def onchange_email_cc(self):
        for record in self:
            if record.model == 'purchase.order':
                record.email_cc = 'purchasing@fischerbell.com'
            else:
                record.email_cc = ''

    @api.onchange('template_id')
    def _onchange_template_id_wrapper(self):
        self.ensure_one()
        if self._context.get("active_model") in {'sale.order', 'purchase.order', 'stock.picking'}:
            atrwork = self.env[self._context.get("active_model")].browse(self._context.get("active_id"))
            if atrwork.artwork_attachment_ids:
                values = self._onchange_template_id(self.template_id.id, self.composition_mode, self.model, self.res_id)[
                    'value']
                if values.get('attachment_ids'):
                    values.get('attachment_ids')[0][2].extend(atrwork.artwork_attachment_ids.ids)
                for fname, value in values.items():
                    setattr(self, fname, value)
            else:
                super(MailComposerMessage, self)._onchange_template_id_wrapper()
        else:
            super(MailComposerMessage, self)._onchange_template_id_wrapper()

    def action_send_mail(self):
        if self._context.get("active_model") == 'purchase.order':
            purchase_order = self.env['purchase.order'].browse(self._context.get("active_id"))
            purchase_order.mail_sended = True 

        if self._context.get("active_model") == 'sale.order':
            sale_id = self.env['sale.order'].browse(self._context.get("active_id"))
            if sale_id and sale_id.state in ('draft','reject'):
                sale_id.action_submit_to_approval() 
        return super(MailComposerMessage, self).action_send_mail()
    
    def get_mail_values(self, res_ids):
        """Generate the values that will be used by send_mail to create mail_messages
        or mail_mails. """
        self.ensure_one()
        results = dict.fromkeys(res_ids, False)
        rendered_values = {}
        mass_mail_mode = self.composition_mode == 'mass_mail'

        # render all template-based value at once
        if mass_mail_mode and self.model:
            rendered_values = self.render_message(res_ids)
        # compute alias-based reply-to in batch
        reply_to_value = dict.fromkeys(res_ids, None)
        if mass_mail_mode and not self.reply_to_force_new:
            records = self.env[self.model].browse(res_ids)
            reply_to_value = records._notify_get_reply_to(default=False)
            # when having no specific reply-to, fetch rendered email_from value
            for res_id, reply_to in reply_to_value.items():
                if not reply_to:
                    reply_to_value[res_id] = rendered_values.get(res_id, {}).get('email_from', False)

        for res_id in res_ids:
            # static wizard (mail.message) values
            mail_values = {
                'subject': self.subject,
                'body': self.body or '',
                'parent_id': self.parent_id and self.parent_id.id,
                'partner_ids': [partner.id for partner in self.partner_ids],
                'attachment_ids': [attach.id for attach in self.attachment_ids],
                'author_id': self.author_id.id,
                'email_from': self.email_from,
                'email_cc': self.email_cc,
                'record_name': self.record_name,
                'reply_to_force_new': self.reply_to_force_new,
                'mail_server_id': self.mail_server_id.id,
                'mail_activity_type_id': self.mail_activity_type_id.id,
                'message_type': 'email' if mass_mail_mode else self.message_type,
            }

            # mass mailing: rendering override wizard static values
            if mass_mail_mode and self.model:
                record = self.env[self.model].browse(res_id)
                mail_values['headers'] = repr(record._notify_by_email_get_headers())
                # keep a copy unless specifically requested, reset record name (avoid browsing records)
                mail_values.update(is_notification=not self.auto_delete_message, model=self.model, res_id=res_id, record_name=False)
                # auto deletion of mail_mail
                if self.auto_delete or self.template_id.auto_delete:
                    mail_values['auto_delete'] = True
                # rendered values using template
                email_dict = rendered_values[res_id]
                mail_values['partner_ids'] += email_dict.pop('partner_ids', [])
                mail_values.update(email_dict)
                if not self.reply_to_force_new:
                    mail_values.pop('reply_to')
                    if reply_to_value.get(res_id):
                        mail_values['reply_to'] = reply_to_value[res_id]
                if self.reply_to_force_new and not mail_values.get('reply_to'):
                    mail_values['reply_to'] = mail_values['email_from']
                # mail_mail values: body -> body_html, partner_ids -> recipient_ids
                mail_values['body_html'] = mail_values.get('body', '')
                mail_values['recipient_ids'] = [Command.link(id) for id in mail_values.pop('partner_ids', [])]

                # process attachments: should not be encoded before being processed by message_post / mail_mail create
                mail_values['attachments'] = [(name, base64.b64decode(enc_cont)) for name, enc_cont in email_dict.pop('attachments', list())]
                attachment_ids = []
                for attach_id in mail_values.pop('attachment_ids'):
                    new_attach_id = self.env['ir.attachment'].browse(attach_id).copy({'res_model': self._name, 'res_id': self.id})
                    attachment_ids.append(new_attach_id.id)
                attachment_ids.reverse()
                mail_values['attachment_ids'] = self.env['mail.thread'].with_context(attached_to=record)._message_post_process_attachments(
                    mail_values.pop('attachments', []),
                    attachment_ids,
                    {'model': 'mail.message', 'res_id': 0}
                )['attachment_ids']

            results[res_id] = mail_values

        results = self._process_state(results)
        return results


    # def get_mail_values(self, res_ids):
    #     """Generate the values that will be used by send_mail to create mail_messages
    #     or mail_mails. """
    #     self.ensure_one()
    #     purchase_order = self.env['purchase.order'].browse(self._context.get("active_id"))
    #     results = dict.fromkeys(res_ids, False)
    #     rendered_values = {}
    #     mass_mail_mode = self.composition_mode == 'mass_mail'
    #
    #     # render all template-based value at once
    #     if mass_mail_mode and self.model:
    #         rendered_values = self.render_message(res_ids)
    #     # compute alias-based reply-to in batch
    #     reply_to_value = dict.fromkeys(res_ids, None)
    #     if mass_mail_mode and not self.reply_to_force_new:
    #         records = self.env[self.model].browse(res_ids)
    #         reply_to_value = records._notify_get_reply_to(default=False)
    #         # when having no specific reply-to, fetch rendered email_from value
    #         for res_id, reply_to in reply_to_value.items():
    #             if not reply_to:
    #                 reply_to_value[res_id] = rendered_values.get(res_id, {}).get('email_from', False)
    #
    #     for res_id in res_ids:
    #         # static wizard (mail.message) values
    #         mail_values = {
    #             'subject': self.subject,
    #             'body': self.body or '',
    #             'parent_id': self.parent_id and self.parent_id.id,
    #             'partner_ids': [partner.id for partner in self.partner_ids],
    #             'attachment_ids': [attach.id for attach in self.attachment_ids],
    #             'author_id': self.author_id.id,
    #             'email_from': self.email_from,
    #             'record_name': self.record_name,
    #             'reply_to_force_new': self.reply_to_force_new,
    #             'mail_server_id': self.mail_server_id.id,
    #             'mail_activity_type_id': self.mail_activity_type_id.id,
    #             'message_type': 'email' if mass_mail_mode else self.message_type,
    #         }
    #         # mass mailing: rendering override wizard static values
    #         # if self._context.get("active_model") == 'purchase.order':
    #         #     mail_values['email_cc'] = purchase_order.user_id.email
    #         if mass_mail_mode and self.model:
    #             record = self.env[self.model].browse(res_id)
    #             mail_values['headers'] = repr(record._notify_by_email_get_headers())
    #             # mail_values['email_cc'] = record.user_id.email
    #             # keep a copy unless specifically requested, reset record name (avoid browsing records)
    #             mail_values.update(is_notification=not self.auto_delete_message, model=self.model, res_id=res_id, record_name=False)
    #             # auto deletion of mail_mail
    #             if self.auto_delete or self.template_id.auto_delete:
    #                 mail_values['auto_delete'] = True
    #             # rendered values using template
    #             email_dict = rendered_values[res_id]
    #             mail_values['partner_ids'] += email_dict.pop('partner_ids', [])
    #             mail_values.update(email_dict)
    #             if not self.reply_to_force_new:
    #                 mail_values.pop('reply_to')
    #                 if reply_to_value.get(res_id):
    #                     mail_values['reply_to'] = reply_to_value[res_id]
    #             if self.reply_to_force_new and not mail_values.get('reply_to'):
    #                 mail_values['reply_to'] = mail_values['email_from']
    #             # mail_mail values: body -> body_html, partner_ids -> recipient_ids
    #             mail_values['body_html'] = mail_values.get('body', '')
    #             mail_values['recipient_ids'] = [Command.link(id) for id in mail_values.pop('partner_ids', [])]
    #
    #             # process attachments: should not be encoded before being processed by message_post / mail_mail create
    #             mail_values['attachments'] = [(name, base64.b64decode(enc_cont)) for name, enc_cont in email_dict.pop('attachments', list())]
    #             attachment_ids = []
    #             for attach_id in mail_values.pop('attachment_ids'):
    #                 new_attach_id = self.env['ir.attachment'].browse(attach_id).copy({'res_model': self._name, 'res_id': self.id})
    #                 attachment_ids.append(new_attach_id.id)
    #             attachment_ids.reverse()
    #             mail_values['attachment_ids'] = self.env['mail.thread'].with_context(attached_to=record)._message_post_process_attachments(
    #                 mail_values.pop('attachments', []),
    #                 attachment_ids,
    #                 {'model': 'mail.message', 'res_id': 0}
    #             )['attachment_ids']
    #         results[res_id] = mail_values
    #
    #     results = self._process_state(results)
    #     return results

