# Copyright 2019 Druidoo - Iván Todorovich
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'POS Order Draft Downpayment',
    'version': '12.0.1.0.0',
    'category': 'Point of Sale',
    'website': 'https://github.com/druidoo/druidoo-addons',
    'author': 'Druidoo',
    'license': 'AGPL-3',
    'depends': [
        'pos_order_mgmt_draft',
    ],
    'data': [
        'views/assets.xml',
        'views/pos_config.xml',
        'views/pos_order.xml',
    ],
    'qweb': [
        'static/src/xml/pos.xml',
    ]
}
