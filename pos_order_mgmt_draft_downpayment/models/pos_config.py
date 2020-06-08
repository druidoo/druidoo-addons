# Copyright 2019 Druidoo - Iván Todorovich
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models, fields


class PosConfig(models.Model):
    _inherit = 'pos.config'

    iface_downpayment = fields.Boolean('Enable Downpayments')
    
    deposit_product_id = fields.Many2one(
        'product.product',
        string='Deposit Product',
        default=_default_deposit_product_id,
    )

    @api.model
    def _default_deposit_product_id(self):
        get_param = self.env['ir.config_parameter'].sudo().get_param
        deposit_product_id = get_param('sale.default_deposit_product_id')
        try:
            deposit_product_id = int(deposit_product_id)
            product = self.env['product.product'].browse(deposit_product_id)
            return product.exists()
        except Exception as e:
            return False
