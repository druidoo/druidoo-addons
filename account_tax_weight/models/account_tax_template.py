# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountTaxTemplate(models.Model):
    _inherit = 'account.tax.template'

    amount_type = fields.Selection(
        selection_add=[
            ('weight', 'Based on product weight')
        ],
    )
