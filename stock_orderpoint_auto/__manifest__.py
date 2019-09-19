# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    'name': 'Stock Orderpoint Automatic',
    'summary': 'Allows to update orderpoints based on time based.',
    'version': '12.0.1.0.0',
    'author': 'Iván Todorovich <ivan.todorovich@druidoo.io>, '
              'Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/stock-logistics-warehouse',
    'category': 'Warehouse Management',
    'depends': [
        'stock',
    ],
    'data': [
        'views/stock_warehouse_orderpoint.xml',
        'data/cron.xml',
    ],
    'license': 'AGPL-3',
}
