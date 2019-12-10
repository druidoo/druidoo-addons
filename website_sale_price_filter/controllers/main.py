from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSalePriceFilter(WebsiteSale):
    ''' Overwrite this controller to support price filters '''

    def _get_search_domain(self, search, category, attrib_values):
        domain = super()._get_search_domain(search, category, attrib_values)
        price_filter = request.context.get('price_filter')
        if price_filter:
            domain += [
                '&',
                ('list_price', '>=', price_filter[0]),
                ('list_price', '<=', price_filter[1]),
            ]
        return domain

    @http.route()
    def shop(self, page=0, category=None, search='', ppg=False, **post):
        # First, we get the maximum price value without filtering
        # We need to do this before altering the context with the price_filter
        attrib_list = request.httprequest.args.getlist('attrib')
        attrib_values = [[int(x) for x in v.split("-")]
                         for v in attrib_list if v]
        domain = self._get_search_domain(search, category, attrib_values)
        price_filter_max = request.env['product.template'].read_group(
            domain=domain,
            fields=['list_price:max'],
            groupby=[],
        )[0].get('list_price')

        # If we have a price_filter, add it to the context
        price_filter = post.get('price_filter')
        if price_filter:
            try:
                price_filter = tuple(map(int, price_filter.split(',')))
                price_filter = (price_filter[0], price_filter[1])
                request.context = dict(request.context,
                                       price_filter=price_filter)
            except Exception:
                pass

        res = super().shop(page, category, search, ppg, **post)

        if price_filter:
            res.qcontext['price_filter'] = price_filter
            res.qcontext['price_min'] = price_filter[0]
            res.qcontext['price_max'] = price_filter[1]
        res.qcontext['price_max_limit'] = price_filter_max
        return res
