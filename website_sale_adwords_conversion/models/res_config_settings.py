from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    google_adwards_conversoin_tracking = fields.Boolean(
        related='website_id.google_adwards_conversoin_tracking',
        readonly=False,
    )
    google_adwords_conversion_key = fields.Char(
        'Tracking ID',
        related='website_id.google_adwords_conversion_key',
        readonly=False,
    )
    google_adwords_event_key = fields.Char(
        'Event ID',
        related='website_id.google_adwords_event_key',
        readonly=False,
    )
