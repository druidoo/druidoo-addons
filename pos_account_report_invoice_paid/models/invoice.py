# Copyright (C) 2020-Today: Druidoo (<http://www.druidoo.io/>)
# @author: Druidoo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html

from odoo import models, fields


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    pos_order_id = fields.One2many(
        'pos.order',
        'invoice_id',
        string='POS Order',
        ondelete='set null',
        readonly=True,
    )
