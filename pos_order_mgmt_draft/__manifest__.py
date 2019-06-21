{
    'name': 'POS Order Draft',
    'version': '12.0.1.0.0',
    'category': 'Point of Sale',
    'website': 'https://github.com/druidoo/druidoo-addons',
    'author': 'Druidoo',
    'license': 'AGPL-3',
    'depends': [
        'pos_order_mgmt',
    ],
    'data': [
        'views/assets.xml',
        'reports/report_pos_order.xml',
    ],
    'qweb': [
        'static/src/xml/pos.xml',
    ]
}
