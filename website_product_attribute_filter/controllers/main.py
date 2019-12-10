from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.website_sale.controllers import main

import logging
_logger = logging.getLogger(__name__)

main.PPG = 18
PPG = main.PPG


class WebsiteSale(WebsiteSale):

    def _get_search_domain_new(self, search, category):
        domain = request.website.sale_product_domain()
        if search:
            for srch in search.split(" "):
                domain += [
                    '|', '|', '|', ('name', 'ilike',
                                    srch), ('description', 'ilike', srch),
                    ('description_sale', 'ilike', srch),
                    ('product_variant_ids.default_code', 'ilike', srch)]

        if category:
            domain += [('public_categ_ids', 'child_of', int(category))]
        return domain

    @http.route()
    def shop(self, page=0, category=None, search='', ppg=False, **post):
        res = super(WebsiteSale, self).shop(
            page, category, search, ppg, **post)
        # Get list of products without attribute filters
        Product = request.env['product.template']
        product_without_filters = Product.search(
            self._get_search_domain_new(search, category))
        # Compute attribute list
        attrib_list = request.httprequest.args.getlist('attrib')
        attrib_values = [[int(x) for x in v.split("-")]
                         for v in attrib_list if v]
        attributes_ids = [v[0] for v in attrib_values]
        attrib_set = [v[1] for v in attrib_values]
        attributes_ids_b = request.env[
            'product.attribute'].browse(set(attributes_ids))
        res.qcontext['appied_filter_result'] = attributes_ids_b
        res.qcontext['applied_filter_values'] = attrib_set
        attrib_category_ids = []
        variant_count = {}

        if product_without_filters:
            attributes_ids_all = request.env['product.attribute'].search(
                [('attribute_line_ids.product_tmpl_id', 'in',
                  product_without_filters.ids)])
        else:
            attributes_ids_all = res.qcontext['attributes']

        # Compute attribute count
        # TODO: Disable if not needed
        domain = self._get_search_domain(search, category, attrib_values)
        domain = [('id', 'in', Product.search(domain).ids)]

        for i in range(len(attributes_ids_all)):
            if attributes_ids_all[i].category_id and \
                    attributes_ids_all[i].value_ids and \
                    len(attributes_ids_all[i].value_ids) > 1 and \
                    attributes_ids_all[i].category_id.id not in \
                    attrib_category_ids:
                attrib_category_ids.append(
                    attributes_ids_all[i].category_id.id)
            for v in attributes_ids_all[i].value_ids:
                actual_domain = domain + \
                    [('attribute_line_ids.value_ids', 'in', [v.id])]
                variant_count.update(
                    {v.id: Product.search_count(actual_domain)})

        res.qcontext['attrib_category'] = request.env[
            'product.attribute.category'].browse(set(attrib_category_ids))
        res.qcontext['variant_counts'] = variant_count
        res.qcontext['shop_category_ids'] = \
            res.qcontext['attributes'] and \
            res.qcontext['attributes'].mapped('category_id').ids or []
        return res
