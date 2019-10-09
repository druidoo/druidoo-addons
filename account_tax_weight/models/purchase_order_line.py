# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.depends('product_qty', 'price_unit', 'taxes_id')
    def _compute_amount(self):
        """
        Override native method to return the product quantity based on its UOM
        """
        for line in self:
            vals = line._prepare_compute_all_values()

            # Convert line product quantity to product uom quantity
            line_product_uom = line.product_uom
            line_product_uom_qty = line.product_qty

            product_uom_qty = line_product_uom_qty
            product_uom = line.product_id.uom_id

            if line_product_uom != product_uom:
                product_uom_qty = line_product_uom._compute_quantity(
                    qty=line_product_uom_qty, to_unit=product_uom)

            taxes = line.taxes_id.with_context(
                product_uom_qty=product_uom_qty).compute_all(
                vals['price_unit'],
                vals['currency_id'],
                vals['product_qty'],
                vals['product'],
                vals['partner'])
            line.update({
                'price_tax': sum(
                    t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })
