from odoo import api, models, fields


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def get_product_multiline_description_sale(self):
        '''
        Override to remove the product reference from the line description.
        Because we'll add the reference on a new column on the reports
        '''
        name = self.name
        if self.description_sale:
            name += '\n' + self.description_sale
        return name
