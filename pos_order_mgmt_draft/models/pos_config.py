# Copyright 2019 Druidoo - Iván Todorovich
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models, fields


class PosConfig(models.Model):
    _inherit = 'pos.config'

    iface_draft_order = fields.Boolean('Create Draft Orders')

    @api.onchange('iface_draft_order')
    def _onchange_iface_draft_order(self):
        if self.iface_draft_order and not self.iface_order_mgmt:
            self.iface_order_mgmt = True
