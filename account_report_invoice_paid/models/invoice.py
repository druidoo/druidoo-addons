# Copyright (C) 2020-Today: Druidoo (<http://www.druidoo.io/>)
# @author: Druidoo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html

from odoo import api, models


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.model
    def _get_payments_vals(self):
        res = super(AccountInvoice, self)._get_payments_vals()
        for data in res:
            payment_id = data.get('account_payment_id')
            if payment_id:
                payment = self.env['account.payment'].browse(payment_id)
                data.update(code=payment.journal_id.code)
        return res
