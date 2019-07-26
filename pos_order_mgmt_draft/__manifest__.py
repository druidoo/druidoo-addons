# Copyright 2019 Druidoo - Iván Todorovich
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'POS Order Draft',
    'summary': 'Create POS draft orders',
    'version': '12.0.1.0.0',
    'category': 'Point of Sale',
    'author': 'Druidoo, '
              'Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/pos',
    'license': 'AGPL-3',
    'maintainers': [
        'ivantodorovich',
    ],
    'depends': [
        'pos_order_mgmt',
    ],
    'data': [
        'views/assets.xml',
        'views/pos_order.xml',
        'views/pos_config.xml',
        'reports/report_pos_order.xml',
        'data/mail_data.xml',
    ],
    'qweb': [
        'static/src/xml/pos.xml',
    ],
}
