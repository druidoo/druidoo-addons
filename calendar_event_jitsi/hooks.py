# Copyright (C) 2020-Today: Druidoo (<https://www.druidoo.io>)
from odoo import api, SUPERUSER_ID

import logging
_logger = logging.getLogger(__name__)

CALENDAR_MAIL_TEMPLATE_REFS = [
    'calendar_template_meeting_invitation',
    'calendar_template_meeting_reminder',
    'calendar_template_meeting_changedate',
]


def pre_init_hook(cr):
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        # Allow to update these templates
        _logger.info('Disabling noupdate on calendar email templates')
        model_data_ids = env['ir.model.data'].search([
            ('model', '=', 'mail.template'),
            ('module', '=', 'calendar'),
            ('name', 'in', CALENDAR_MAIL_TEMPLATE_REFS),
        ]).write({
            'noupdate': False,
        })


def post_init_hook(cr, registry):
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        # Revert noupdate change
        _logger.info('Enabling noupdate on calendar email templates')
        model_data_ids = env['ir.model.data'].search([
            ('model', '=', 'mail.template'),
            ('module', '=', 'calendar'),
            ('name', 'in', CALENDAR_MAIL_TEMPLATE_REFS),
        ]).write({
            'noupdate': False,
        })
        # Force the reload of translations, because they are
        # somehow not loaded.
        _logger.info('Forcing reload of translations on calendar email templates')
        mods = env.ref('base.module_calendar_event_jitsi')
        mods.with_context(overwrite=True)._update_translations('fr_FR')
