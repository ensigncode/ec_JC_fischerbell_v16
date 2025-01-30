from odoo import models, fields, api
from odoo.exceptions import UserError

class MailActivity(models.Model):
    _inherit = 'mail.activity'

    user_group_id = fields.Many2one('res.groups', string="User Group")
    user_ids = fields.Many2many('res.users', string="Users")


    @api.model_create_multi
    def create(self, vals_list):
        # Call the original create method for the base records
        res = super(MailActivity, self).create(vals_list)
        res_model = self._context.get('default_res_model')

        if res_model in ["sale.order", "purchase.order"]:
            activities = self.env['mail.activity']
            additional_vals = []

            for vals in vals_list:
                user_ids = vals.pop('user_ids', False)
                if user_ids:
                    # Prepare additional activities for each user
                    for user_id in user_ids[0][2]:  # Extract list of user IDs
                        if user_id != vals.get('user_id'):
                            user_vals = vals.copy()
                            user_vals['user_id'] = user_id
                            additional_vals.append(user_vals)

            # Create all additional activities in a single call
            if additional_vals:
                activities = super(MailActivity, self).create(additional_vals)

            # Combine original and additional activities
            all_activities = res + activities

            # Notify users for non-automated activities
            activities_to_notify = all_activities.filtered(lambda act: act.user_id != self.env.user and not act.automated)
            activities_to_notify._check_access_assignation()

            if activities_to_notify:
                # Separate sudo and normal notifications
                readable_user_partners = self.env.user.partner_id
                to_sudo = activities_to_notify.filtered(
                    lambda act: act.user_id.partner_id not in readable_user_partners
                )
                other = activities_to_notify - to_sudo
                to_sudo.sudo().action_notify()
                other.action_notify()

            # Subscribe users to models
            activities_by_model = all_activities._classify_by_model()
            for model, activity_data in activities_by_model.items():
                per_user = {}
                for activity in activity_data['activities'].filtered(lambda act: act.user_id):
                    if activity.user_id not in per_user:
                        per_user[activity.user_id] = [activity.res_id]
                    else:
                        per_user[activity.user_id].append(activity.res_id)
                
                for user, res_ids in per_user.items():
                    readable_partners = (
                        user.partner_id.ids if user.partner_id in readable_user_partners else user.sudo().partner_id.ids
                    )
                    self.env[model].browse(res_ids).message_subscribe(partner_ids=readable_partners)

            # Send notifications for activities with a deadline
            todo_activities = all_activities.filtered(lambda act: act.date_deadline <= fields.Date.today())
            if todo_activities:
                self.env['bus.bus']._sendmany([
                    (activity.user_id.partner_id, 'mail.activity/updated', {'activity_created': True})
                    for activity in todo_activities
                ])

        return res

    @api.onchange('user_group_id')
    def _onchange_user_group_id(self):
        """Populate users field based on the selected group."""
        if self.user_group_id:
            user_ids = self.env['res.users'].search([('groups_id', '=', self.user_group_id.id)])
            self.user_ids = user_ids
        else:
            self.user_ids = False
