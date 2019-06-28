# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Account Tax Weight',
    'version': '1.0',
    'category': 'Accounting',
    'description': """
Allows tax computation based on product.weight
    """,
    'author': 'Druidoo',
    'website': 'https://druidoo.io/',
    'depends': [
        'account',
        'product',
        'purchase',
        'sale',
    ],
    'data': [
        'views/account_tax_views.xml',
    ],

    'test': [],
    'demo': [],
    'installable': True,
    'active': False,
    'application': False,
}
