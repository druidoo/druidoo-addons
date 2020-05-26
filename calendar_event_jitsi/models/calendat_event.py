# Copyright (C) 2020-Today: Druidoo (<https://www.druidoo.io>)

from odoo import models, fields, api
from odoo.addons.http_routing.models.ir_http import slug


class Meeting(models.Model):
    _inherit = 'calendar.event'

    jitsi_meet_url = fields.Char(
        string="Jitsi Meet URL",
        readonly=True,
        help="Jitsi Meet URL"
    )

    @api.model
    def create(self, values):
        meeting = super(Meeting, self).create(values)
        meeting.jitsi_meet_url = "https://meet.jit.si/%s" % slug(meeting)
        return meeting
