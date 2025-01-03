# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, Command, fields, models, tools, SUPERUSER_ID, _, _lt
from odoo.osv import expression


class AccountTaxReportActivity(models.Model):
    _inherit = "mail.activity"

    def _get_mail_activity_domain(self, domain, active_user):
        mail_activity_records = self.with_user(SUPERUSER_ID).search([])
        filtered_records = mail_activity_records.filtered(lambda activity: (
            activity.user_id and activity.user_id.employee_id and 
            activity.user_id.employee_id.parent_id and 
            activity.user_id.employee_id.parent_id.user_id == active_user
        ) or (
            activity.create_uid and activity.create_uid.employee_id and 
            activity.create_uid.employee_id.parent_id and 
            activity.create_uid.employee_id.parent_id.user_id == active_user
        ))
        mail_activity_ids = list(filtered_records.ids)
        return expression.OR([domain, [('id', 'in', mail_activity_ids)]])

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        if 'activity_list_view' in self.env.context and not self.env.user.has_group('base.group_system'):
            domain = ['|', ('user_id', '=', self.env.user.id), ('create_uid', '=', self.env.user.id)]
            domain = self._get_mail_activity_domain(domain, self.env.user)
        return super().read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        if 'activity_list_view' in self.env.context and not self.env.user.has_group('base.group_system'):
            domain = ['|', ('user_id', '=', self.env.user.id), ('create_uid', '=', self.env.user.id)]
            domain = self._get_mail_activity_domain(domain, self.env.user)
        return super().search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)
