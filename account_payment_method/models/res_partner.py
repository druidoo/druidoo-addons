from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    property_payment_journal_id = fields.Many2one(
        'account.journal',
        'Payment method',
        domain=[('type', 'in', ['bank', 'cash'])],
        company_dependent=True,
    )

    property_supplier_payment_journal_id = fields.Many2one(
        'account.journal',
        'Payment method',
        domain=[('type', 'in', ['bank', 'cash'])],
        company_dependent=True,
    )
