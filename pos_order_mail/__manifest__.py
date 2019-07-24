{
    'name': 'POS Order Mail',
    'version': '12.0.1.0.0',
    'category': 'Point of Sale',
    'website': 'https://github.com/druidoo/druidoo-addons',
    'author': 'Druidoo',
    'license': 'AGPL-3',
    'depends': [
        'point_of_sale',
        'mail',
    ],
    'data': [
        'views/assets.xml',
        'views/pos_config.xml',
    ],
    'qweb': [
        'static/src/xml/pos.xml',
    ]
}
