from odoo import api, models, fields


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.depends('order_id.force_invoice_status')
    def _compute_invoice_status(self):
        super()._compute_invoice_status()
        for line in self:
            if line.order_id.state not in ['sale', 'done']:
                continue
            if line.order_id.force_invoice_status:
                line.invoice_status = line.order_id.force_invoice_status
