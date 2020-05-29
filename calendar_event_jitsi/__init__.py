# Copyright (C) 2020-Today: Druidoo (<https://www.druidoo.io>)

from . import models
from odoo import api, SUPERUSER_ID


def pre_init_hook(cr):
    env = api.Environment(cr, SUPERUSER_ID, {})
    tempalte_ids = env.ref(
        'calendar.calendar_template_meeting_invitation'
    )
    tempalte_ids |= env.ref(
        'calendar.calendar_template_meeting_reminder'
    )
    tempalte_ids |= env.ref(
        'calendar.calendar_template_meeting_changedate'
    )
    model_data_ids = env['ir.model.data'].search([
        ('model', '=', 'mail.template'),
        ('module', '=', 'calendar'),
        ('res_id', 'in', tempalte_ids.ids)
    ])
    model_data_ids.noupdate = False


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    mods = env.ref('base.module_calendar_event_jitsi')
    mods.with_context(overwrite=True)._update_translations('fr_FR')
