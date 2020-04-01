from odoo import models, fields


class Website(models.Model):
    _inherit = 'website'

    google_adwords_conversion_tracking = fields.Boolean()
    google_adwords_conversion_key = fields.Char('Tracking ID')
    google_adwords_conversion_event_key = fields.Char('Event ID')
