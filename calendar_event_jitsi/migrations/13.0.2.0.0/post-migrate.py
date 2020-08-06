# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        mods = env.ref('base.module_calendar_event_jitsi')
        mods.with_context(overwrite=True)._update_translations('fr_FR')
