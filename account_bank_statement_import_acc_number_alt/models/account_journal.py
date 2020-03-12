from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    bank_acc_number_alt = fields.Char(related="bank_account_id.acc_number_alt")
