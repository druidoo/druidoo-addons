from odoo import api, models, fields


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    force_invoice_status = fields.Selection([
        ('no', 'Nothing to Bill'),
        ('invoiced', 'No Bill to Receive'),
        ],
        help='If selected, it\'ll force the invoice status of the lines.',
        track_visibility='onchange',
        copy=False,
    )

    @api.depends('force_invoice_status')
    def _get_invoiced(self):
        super()._get_invoiced()
        for order in self:
            if order.state not in ['purchase', 'done']:
                continue
            if order.force_invoice_status:
                order.invoice_status = order.force_invoice_status
