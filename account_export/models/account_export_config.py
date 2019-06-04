# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountExportConfig(models.Model):
    _name = 'account.export.config'

    name = fields.Char(required=True)

    header = fields.Char(
        help='Header of the exported file.\n'
             'Exemple: journal,account,ref,amount',
    )

    footer = fields.Char(
        help='Footer of the exported file.\n'
             'Example: END',
    )

    csv_separator = fields.Char('Separator', required=True, default=';')

    dateformat = fields.Char(
        string='Software Date Format',
        help="""
        %d: day on 2 digits
        %m: month on 2 digits
        %y: year on 2 digits
        %Y: year on 4 digits
        exemple: %d%m%y -> 211216""",
        default='%d%m%y',
        required=True,
    )

    is_default = fields.Boolean('Is Default')
    active = fields.Boolean('active', default=True)

    credit_debit_format = fields.Selection([
        ('01', 'Debit: 0; Credit: 1'),
        ('DC', 'Debit: D; Credit: C'),
        ('-+', 'Debit: (+); Credit: (-)'),
        ('+-', 'Debit: (-); Credit: (+)'),
        ],
        string='Credit and Debit',
        default='01',
        required=True,
    )

    show_account_name = fields.Boolean('Account Name', default=False)
    show_partner_ref = fields.Boolean('Partner Reference', default=False)
    show_partner_name = fields.Boolean('Partner Name', default=False)
    show_product_code = fields.Boolean('Product Reference', default=False)
    show_move_line_name = fields.Boolean('Move Line Name', default=False)
