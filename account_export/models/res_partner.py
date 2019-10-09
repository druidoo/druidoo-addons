# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    property_account_receivable_software = fields.Char(
        'Account Receivable (software)', size=17,
        help='Receivable account in your accounting software')
    property_account_payable_software = fields.Char(
        'Account Payable (software)', size=17,
        help='Payable account in your accounting software')
