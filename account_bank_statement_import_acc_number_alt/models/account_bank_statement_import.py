from odoo import models


class AccountBankStatementImport(models.TransientModel):
    _inherit = 'account.bank.statement.import'

    def _check_journal_bank_account(self, journal, account_number):
        res = super()._check_journal_bank_account(journal, account_number)
        return res or journal.bank_account_id.acc_number_alt == account_number
