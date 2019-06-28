# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def get_taxes_values(self):
        """
        Override native method to compute tax amount based on product UOM
        """
        tax_grouped = {}
        round_curr = self.currency_id.round
        for line in self.invoice_line_ids:
            if not line.account_id:
                continue
            price_unit = line.price_unit * (1 - (line.discount or 0.0) / 100.0)

            # Convert line product quantity to product uom quantity
            line_product_uom = line.uom_id
            line_product_uom_qty = line.quantity

            product_uom_qty = line_product_uom_qty
            product_uom = line.product_id.uom_id

            if line_product_uom != product_uom:
                product_uom_qty = line_product_uom._compute_quantity(
                    qty=line_product_uom_qty, to_unit=product_uom)

            taxes = line.invoice_line_tax_ids.with_context(
                product_uom_qty=product_uom_qty).compute_all(
                    price_unit,
                    self.currency_id,
                    line_product_uom_qty,
                    line.product_id,
                    self.partner_id
            )['taxes']
            for tax in taxes:
                val = self._prepare_tax_line_vals(line, tax)
                key = self.env['account.tax'].browse(
                    tax['id']).get_grouping_key(val)

                if key not in tax_grouped:
                    tax_grouped[key] = val
                    tax_grouped[key]['base'] = round_curr(val['base'])
                else:
                    tax_grouped[key]['amount'] += val['amount']
                    tax_grouped[key]['base'] += round_curr(val['base'])
        return tax_grouped
