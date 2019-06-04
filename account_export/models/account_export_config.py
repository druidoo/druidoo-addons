# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountExportConfig(models.Model):
    _name = 'account.export.config'

    name = fields.Char('Name', required=True)
    header = fields.Char("Header", help="""Header of the exported file.
        exemple: journal,account,ref,amount""")
    footer = fields.Char("Footer", help="""Footer of the exported file.
        exemple: END""")
    csv_separator = fields.Char('Separator', required=True)
    dateformat = fields.Char(
        string='Software Date Format',
        help="""
        %d: day on 2 digits
        %m: month on 2 digits
        %y: year on 2 digits
        %Y: year on 4 digits
        exemple: %d%m%y -> 211216""")
    is_default = fields.Boolean('Is Default')
    active = fields.Boolean('active', default=True)

    credit_debit_format = fields.Selection([
        ('01', 'Debit: 0; Credit: 1'),
        ('DC', 'Debit: D; Credit: C'),
        ('-+', 'Debit: (+); Credit: (-)'),
        ('+-', 'Debit: (-); Credit: (+)'),
        ],
        string='Credit and Debit format',
        default='01',
        required=True,
    )
