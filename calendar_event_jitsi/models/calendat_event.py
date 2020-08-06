# Copyright (C) 2020-Today: Druidoo (<https://www.druidoo.io>)

from odoo import models, fields, api
from odoo.addons.http_routing.models.ir_http import slug

JITSI_MEET_BASE_URL = "https://meet.jit.si"


class Meeting(models.Model):
    _inherit = 'calendar.event'

    jitsi_meet_url = fields.Char(
        string="Jitsi Meet URL",
        compute="_compute_jitsi_meet_url",
    )

    def _compute_jitsi_meet_url(self):
        for rec in self:
            rec.jitsi_meet_url = "%s/%s" % (
                JITSI_MEET_BASE_URL, slug(rec))
