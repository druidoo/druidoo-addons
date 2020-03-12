from odoo import fields, models


class Bank(models.Model):
    _inherit = "res.partner.bank"

    acc_number_alt = fields.Char(
        "Alternative Account Number",
        help=(
            "Alternative Bank Account Number\n"
            "It will be considered when importing bank statements, if "
            "the primary account number doesn't match."
        ),
    )
