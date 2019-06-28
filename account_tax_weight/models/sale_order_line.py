# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.multi
    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        """
        Compute the amounts of the sale order line based on product UOM.
        """
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)

            # Convert line product quantity to product uom quantity
            line_product_uom = line.product_uom
            line_product_uom_qty = line.product_uom_qty

            product_uom = line.product_id.uom_id
            product_uom_qty = line_product_uom_qty

            if line_product_uom != product_uom:
                product_uom_qty = line_product_uom._compute_quantity(
                    qty=line_product_uom_qty, to_unit=product_uom)
            taxes = line.tax_id.with_context(
                product_uom_qty=product_uom_qty).compute_all(
                    price,
                    line.order_id.currency_id,
                    line_product_uom_qty,
                    product=line.product_id,
                    partner=line.order_id.partner_shipping_id
                )
            line.update({
                'price_tax': sum(
                    t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })
