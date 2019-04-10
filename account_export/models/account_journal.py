# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    export_code = fields.Char(
        'Export Account Code', size=6,
        help="Code of this journal in your accounting software")
    group_fields = fields.Many2many(
        string='Group export by', comodel_name='ir.model.fields',
        domain=[('model', '=', 'account.move.line')],
        help="""If you specify fields here, they will be used to group the
        move lines in the generated exported file.""")
