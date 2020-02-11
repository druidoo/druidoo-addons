from odoo import fields, models


class PosVoucherType(models.Model):
    _name = 'pos.voucher.type'
    _description = 'POS Voucher Type'

    name = fields.Char('Type', required=True)
    journal_id = fields.Many2one(
        'account.journal',
        string='Journal',
        required=True,
        domain=[('is_voucher', '=', True)],
        context={
            'default_type': 'cash',
            'default_is_voucher': True,
            'default_journal_user': True,
        },
    )
    sequence_id = fields.Many2one(
        'ir.sequence',
        string='Sequence',
        required=True,
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        domain=[
            ('available_in_pos', '=', True),
            ('type', '=', 'service')
        ],
        context={
            'default_available_in_pos': True,
            'default_type': 'service',
        }
    )
