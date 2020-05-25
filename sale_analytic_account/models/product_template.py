from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    create_analytic_account = fields.Boolean(string='Create Analytic Account')
