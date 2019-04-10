from odoo import api, fields, models
from collections import OrderedDict


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    payment_journal_id = fields.Many2one(
        'account.journal',
        'Payment method',
        states={'draft': [('readonly', False)]},
    )

    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self):
        partner_id = False
        if self.partner_id:
            partner_id = self.partner_id.commercial_partner_id
        if partner_id and self.company_id:
            partner_id = \
                partner_id.with_context(force_company=self.company_id.id)
        if partner_id:
            if self.type in ['out_invoice', 'out_refund']:
                self.payment_journal_id = \
                    partner_id.property_payment_journal_id.id
            else:
                self.payment_journal_id = \
                    partner_id.property_supplier_payment_journal_id.id
        return super(AccountInvoice, self)._onchange_partner_id()

    @api.multi
    @api.constrains('company_id', 'payment_journal_id')
    def _check_payment_journal_id(self):
        for rec in self:
            if (
                rec.payment_journal_id
                and rec.payment_journal_id.company_id != rec.company_id
            ):
                raise UserError(_(
                    'The payment method should belong to the '
                    'same company as the invoice.'))

    def _get_onchange_create(self):
        """ Add payment_journal_id to the list """
        res = super(AccountInvoice, self)._get_onchange_create()
        res.get('_onchange_partner_id').append('payment_journal_id')
        return res

    def _get_refund_common_fields(self):
        """ Add payment_journal_id to the list of fields for refunds """
        res = super(AccountInvoice, self)._get_refund_common_fields()
        res.append('payment_journal_id')
        return res
