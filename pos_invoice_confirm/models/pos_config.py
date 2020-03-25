# Copyright 2019 Druidoo - Iván Todorovich
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class PosConfig(models.Model):
    _inherit = 'pos.config'

    iface_invoice_order_confirm = fields.Boolean(
        'Invoice reminder',
        help=(
            'If the order is not set to be invoiced, and the user '
            'tries to validate it, it\'ll show a confirmation popup '
            'asking the user if he wants to invoice it or not.\n\n'
            'This popup will not be shown if the order doesn\'t '
            'have a customer set.'
        ),
    )

    @api.onchange('module_account')
    def _onchange_module_account(self):
        super()._onchange_module_account()
        if not self.module_account:
            self.iface_invoice_order_confirm = False
