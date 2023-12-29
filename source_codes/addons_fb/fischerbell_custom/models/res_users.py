from odoo import _, api, fields, models, registry, tools
from odoo.tools import is_html_empty
from markupsafe import Markup


class ResUser(models.Model):
    _inherit = "res.users"

    email_signature_option = fields.Selection([('base', 'Normal'),
                                               ('custom_brand', 'Customize With Brand'),
                                               ('custom_without_brand', 'Customize Without Brand')],
                                              string="Email Signature Option", default='base')

    @api.depends('name', 'email_signature_option')
    def _compute_signature(self):
        for user in self.filtered(lambda user: user.name):

            if user.email_signature_option == 'custom_brand':
                user.signature = Markup(f'''<table align="left">
                    <tbody>
                        <tr>
                            <td rowspan="3" style="width: 145px;">
                                <p class="mb-0"><img alt="fischerbell_1" id="fischerbell_1" src="/fischerbell_custom/static/src/img/fischerbell1.png" style="height:120px; width:140px" /></p>
                            </td>
                            <td colspan="3" style="width: 600px;height: 50px;">
                                <h1>&nbsp;&nbsp;{user['name']} | {user['partner_id']['function']}</h1>
                            </td>
                        </tr>
                        <tr>
                            <td colspan="3">
                                <h2>&nbsp;&nbsp; <img alt="calling_1" id="calling_1" src="/fischerbell_custom/static/src/img/calling.png" style="height:25px; width:25px" /> {user['company_id']['phone']} | <img alt="calling_2" id="calling_2" src="/fischerbell_custom/static/src/img/calling.png" style="height:25px; width:25px" /> {user['company_id']['mobile']} | <img alt="email" id="email" src="/fischerbell_custom/static/src/img/email.png" style="height:25px; width:25px" /> {user['company_id']['email']}</h2 >
                            </td>
                        </tr>
                        <tr>
                            <td colspan="3">
                                <p class="mb-0" style="margin-left: 15px;"><strong>{user['company_id']['name']}</strong></p>
                                <p class="mb-0">
                                <span style="display: block; width: 380px !important; margin-left: 15px;"> {user['company_id']['street']} {user['company_id']['street2']} {user['company_id']['city']} {user['company_id']['state_id']['name']} {user['company_id']['country_id']['name']} {user['company_id']['zip']}</span>
                                <span class="float-end mt-n4" style="float: right; margin-top: -40px !important;">
                                    <a href="{user['company_id']['social_facebook']}" class="s_social_media_facebook" target="_blank">
                                        <img alt="fischerbell_fb" id="fischerbell_fb" src="/fischerbell_custom/static/src/img/fischerbell4.png" style="height:25px; width:25px" />
                                    </a>
                                    <a href="{user['company_id']['social_facebook']}" class="s_social_media_instagram" target="_blank">
                                        <img alt="fischerbell_fb" id="fischerbell_fb" src="/fischerbell_custom/static/src/img/fischerbell_fb.png" style="height:25px; width:25px" />
                                    </a>
                                    <a href="{user['company_id']['social_facebook']}" class="s_social_media_twitter" target="_blank">
                                        <img alt="fischerbell_4" id="fischerbell_4" src="/fischerbell_custom/static/src/img/fischerbell_insta.png" style="height:25px; width:25px" />
                                    </a>
                                    <a href="{user['company_id']['social_facebook']}" class="s_social_media_linkedin" target="_blank">
                                        <img alt="fischerbell_fb" id="fischerbell_fb" src="/fischerbell_custom/static/src/img/fischerbell_in.png" style="height:25px; width:25px" />
                                    </a>
                                    <a href="{user['company_id']['social_facebook']}" class="s_social_media_instagram" target="_blank">
                                        <img alt="fischerbell_fb" id="fischerbell_fb" src="/fischerbell_custom/static/src/img/fischerbell_store.png" style="height:25px; width:25px" />
                                    </a>
                                    <a href="{user['company_id']['social_facebook']}" class="s_social_media_twitter" target="_blank">
                                        <img alt="fischerbell_4" id="fischerbell_4" src="/fischerbell_custom/static/src/img/fischerbell_laz.png" style="height:25px; width:25px" />
                                    </a>
                                    <a href="{user['company_id']['social_facebook']}" class="s_social_media_linkedin" target="_blank">
                                        <img alt="fischerbell_fb" id="fischerbell_fb" src="/fischerbell_custom/static/src/img/fischerbell_sopy.png" style="height:25px; width:25px" />
                                    </a>
                                </span>
                                </p>
                            </td>
                        </tr>
                         <tr>
                            <td colspan="4">
                                <p><img alt="fischerbell_safety" id="fischerbell_safety" src="/fischerbell_custom/static/src/img/fischerbell_safety.png" style="height:40px; width:745px" /></p>
                            </td>
                        </tr>
                         <tr>
                            <td colspan="4">
                                <p><img alt="fischerbell_3" id="fischerbell_3" src="/fischerbell_custom/static/src/img/fischerbell3.png" style="height:120px; width:745px" /></p>
                            </td>
                        </tr>
                    </tbody>
                </table>''')
            elif user.email_signature_option == 'custom_without_brand':
                user.signature = Markup(f'''<table align="left">
                    <tbody>
                        <tr>
                            <td rowspan="3" style="width: 145px;">
                                <p class="mb-0"><img alt="fischerbell_1" id="fischerbell_1" src="/fischerbell_custom/static/src/img/fischerbell1.png" style="height:120px; width:140px" /></p>
                            </td>
                            <td colspan="3" style="width: 600px;height: 50px;">
                                <h1>&nbsp;&nbsp;{user['name']} | {user['partner_id']['function']}</h1>
                            </td>
                        </tr>
                        <tr>
                            <td colspan="3">
                                <h2>&nbsp;&nbsp; <img alt="calling_1" id="calling_1" src="/fischerbell_custom/static/src/img/calling.png" style="height:25px; width:25px" /> {user['company_id']['phone']} | <img alt="calling_2" id="calling_2" src="/fischerbell_custom/static/src/img/calling.png" style="height:25px; width:25px" /> {user['company_id']['mobile']} | <img alt="email" id="email" src="/fischerbell_custom/static/src/img/email.png" style="height:25px; width:25px" /> {user['company_id']['email']}</h2 >
                            </td>
                        </tr>
                        <tr>
                            <td colspan="3">
                                <p class="mb-0" style="margin-left: 15px;"><strong>{user['company_id']['name']}</strong></p>
                                <p class="mb-0">
                                <span style="display: block; width: 380px !important; margin-left: 15px;"> {user['company_id']['street']} {user['company_id']['street2']} {user['company_id']['city']} {user['company_id']['state_id']['name']} {user['company_id']['country_id']['name']} {user['company_id']['zip']}</span>
                                <span class="float-end mt-n4" style="float: right; margin-top: -40px !important;">
                                    <a href="{user['company_id']['social_facebook']}" class="s_social_media_facebook" target="_blank">
                                        <img alt="fischerbell_fb" id="fischerbell_fb" src="/fischerbell_custom/static/src/img/fischerbell4.png" style="height:25px; width:25px" />
                                    </a>
                                    <a href="{user['company_id']['social_facebook']}" class="s_social_media_instagram" target="_blank">
                                        <img alt="fischerbell_fb" id="fischerbell_fb" src="/fischerbell_custom/static/src/img/fischerbell_fb.png" style="height:25px; width:25px" />
                                    </a>
                                    <a href="{user['company_id']['social_facebook']}" class="s_social_media_twitter" target="_blank">
                                        <img alt="fischerbell_4" id="fischerbell_4" src="/fischerbell_custom/static/src/img/fischerbell_insta.png" style="height:25px; width:25px" />
                                    </a>
                                    <a href="{user['company_id']['social_facebook']}" class="s_social_media_linkedin" target="_blank">
                                        <img alt="fischerbell_fb" id="fischerbell_fb" src="/fischerbell_custom/static/src/img/fischerbell_in.png" style="height:25px; width:25px" />
                                    </a>
                                    <a href="{user['company_id']['social_facebook']}" class="s_social_media_instagram" target="_blank">
                                        <img alt="fischerbell_fb" id="fischerbell_fb" src="/fischerbell_custom/static/src/img/fischerbell_store.png" style="height:25px; width:25px" />
                                    </a>
                                    <a href="{user['company_id']['social_facebook']}" class="s_social_media_twitter" target="_blank">
                                        <img alt="fischerbell_4" id="fischerbell_4" src="/fischerbell_custom/static/src/img/fischerbell_laz.png" style="height:25px; width:25px" />
                                    </a>
                                    <a href="{user['company_id']['social_facebook']}" class="s_social_media_linkedin" target="_blank">
                                        <img alt="fischerbell_fb" id="fischerbell_fb" src="/fischerbell_custom/static/src/img/fischerbell_sopy.png" style="height:25px; width:25px" />
                                    </a>
                                </span>
                                </p>
                            </td>
                        </tr>
                         <tr>
                            <td colspan="4">
                                <p><img alt="fischerbell_safety" id="fischerbell_safety" src="/fischerbell_custom/static/src/img/fischerbell_safety.png" style="height:40px; width:745px" /></p>
                            </td>
                        </tr>
                    </tbody>
                </table>''')
            else:
                user.signature = Markup('<p>--&--<br />%s</p>') % user['name']



