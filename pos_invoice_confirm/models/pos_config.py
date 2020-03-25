# Copyright 2019 Druidoo - Iván Todorovich
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields


class PosConfig(models.Model):
    _inherit = 'pos.config'

    iface_invoice_order_reminder = fields.Boolean(
        'Show invoice order reminder')
