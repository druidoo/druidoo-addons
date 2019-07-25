from odoo import api, models, fields


class PosConfig(models.Model):
    _inherit = 'pos.config'

    deposit_product_id = fields.Many2one(
        'product.product',
        string='Deposit Product',
        default=lambda self:
            self.env['product.product'].browse(
                self.env['ir.config_parameter'].sudo().get_param(
                    'sale.default_deposit_product_id')).exists()
    )
