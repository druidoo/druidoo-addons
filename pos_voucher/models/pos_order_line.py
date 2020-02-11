from odoo import fields, models


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    voucher_type_id = fields.Many2one(
        'pos.voucher.type',
        'Voucher Type',
    )
    pos_voucher_id = fields.Many2one(
        'pos.voucher',
        'POS Voucher',
    )
    pos_voucher_code = fields.Char(
        'POS voucher code',
        default='/',
        copy=False,
        help='this is for update from pos screen to '
             'display in pos voucher ticket',
    )
