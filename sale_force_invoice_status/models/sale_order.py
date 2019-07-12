from odoo import models, fields


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    force_invoice_status = fields.Selection([
        ('no', 'Nothing to Invoice'),
        ('invoiced', 'Fully Invoiced'),
        ],
        help='If selected, it\'ll force the invoice status of the lines. '
             'It has no impact on the to_invoice_qty field.',
        track_visibility='onchange',
        copy=False,
    )
