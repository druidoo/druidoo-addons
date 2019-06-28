# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountTax(models.Model):
    _inherit = 'account.tax'

    amount_type = fields.Selection(
        selection_add=[
            ('weight', 'Based on product weight')
        ],
    )

    @api.multi
    def _compute_amount(
            self, base_amount, price_unit,
            quantity=1.0, product=None, partner=None):
        """
        Override native method to compute tax based on product weight
        """
        self.ensure_one()

        if self.amount_type == 'weight':
            if not product:
                display_name = self.name_get()[0][1]
                raise UserError(
                    _('Tax {} requires product to compute amount '
                      'based on product weight'.format(display_name)))
            product_uom_qty = self._context.get('product_uom_qty', quantity)
            tax_amount = product.weight * self.amount * product_uom_qty
            return tax_amount
        return super(AccountTax, self)._compute_amount(
            base_amount=base_amount,
            price_unit=price_unit,
            quantity=quantity,
            product=product,
            partner=partner
        )
