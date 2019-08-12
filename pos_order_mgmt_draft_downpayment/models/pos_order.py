# Copyright 2019 Druidoo - Iván Todorovich
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models, fields


class PosOrder(models.Model):
    _inherit = 'pos.order'

    downpayment_order_id = fields.Many2one(
        'pos.order',
        string='Downpayment for Order',
        help='The order that is being paid',
    )

    downpayment_order_ids = fields.One2many(
        'pos.order',
        'downpayment_order_id',
        string='Downpayments',
        help='Downpayment Orders',
        readonly=True,
    )

    @api.model
    def _order_fields(self, ui_order):
        res = super()._order_fields(ui_order)
        res['downpayment_order_id'] = ui_order.get('downpayment_order_id')
        return res
