{
    'name': 'Stock Lot numbers in Invoice report',
    'summary': '',
    'version': '12.0.1.0.0',
    'category': 'Accounting & Finance',
    'author': "Druidoo",
    'website': 'http://www.druidoo.io',
    'license': "AGPL-3",
    'depends': [
        'sale_stock',
    ],
    'data': [
        'security/account_invoice_security.xml',
        'views/res_config_settings_views.xml',
        'views/report_invoice.xml',
    ],
}
