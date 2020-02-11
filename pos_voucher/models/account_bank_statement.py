from odoo import fields, models


class AccountBankStatement(models.Model):
    _inherit = 'account.bank.statement'

    is_voucher = fields.Boolean(
        related='journal_id.is_voucher',
        store=True,
    )
