# Copyright 2019 Druidoo - Iván Todorovich
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields


class PosConfig(models.Model):
    _inherit = 'pos.config'

    iface_downpayment = fields.Boolean('Enable Downpayments')

    deposit_product_id = fields.Many2one(
        'product.product',
        string='Deposit Product',
        default=lambda self:
            self.env['product.product'].browse(
                self.env['ir.config_parameter'].sudo().get_param(
                    'sale.default_deposit_product_id')).exists()
    )
