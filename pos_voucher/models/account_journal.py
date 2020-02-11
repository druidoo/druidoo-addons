from odoo import api, fields, models


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    is_voucher = fields.Boolean('Use as a Voucher')

    @api.onchange('journal_user', 'type')
    def onchange_journal_user_type(self):
        if not self.journal_user:
            self.is_voucher = False
