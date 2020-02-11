from odoo import api, fields, models


class POSVoucherHistory(models.Model):
    _name = 'pos.voucher.history'
    _description = 'POS Voucher History'

    pos_voucher_id = fields.Many2one(
        'pos.voucher',
        'Voucher',
        required=True,
        ondelete='cascade',
    )
    consumed_date = fields.Datetime(required=True)
    amount = fields.Monetary(required=True)
    currency_id = fields.Many2one(related='pos_voucher_id.currency_id')

    @api.model
    def create(self, vals):
        history = super().create(vals)
        history.pos_voucher_id.action_consume()
        return history
