from odoo import models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for so in self:
            if so.order_line.filtered(
                    lambda line: line.product_id.create_analytic_account):
                analytic_account_id = \
                    self.env['account.analytic.account'].create({
                        'name': so.name,
                        'partner_id': so.partner_id.id
                    })
                so.analytic_account_id = analytic_account_id
        return res
