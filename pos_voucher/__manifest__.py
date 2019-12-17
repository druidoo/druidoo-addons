{
    'name': 'POS Voucher',
    'summary': '',
    'version': '12.0.1.0.0',
    'category': 'Druidoo POS',
    'website': 'https://github.com/druidoo/druidoo-addons',
    'author': 'Druidoo',
    'license': 'AGPL-3',
    'depends': [
        'point_of_sale',
    ],
    'data': [
        'security/pos_voucher_security.xml',
        'security/ir.model.access.csv',
        'report/pos_voucher_report.xml',
        'report/report.xml',
        'views/pos_voucher_views.xml',
        'data/data.xml',
        'views/templates.xml',
    ],
    'qweb': [
        'static/src/xml/pos.xml',
    ],
}
