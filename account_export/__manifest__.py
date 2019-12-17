{
    'name': 'Account Export',
    "summary": "Export account move lines for accounting software",
    'version': '12.0.2.0.0',
    "category": 'Accounting & Finance',
    "author": "Druidoo",
    'website': 'http://www.druidoo.io',
    "license": "AGPL-3",
    "depends": [
        'base',
        'account',
        'document',
        'mail',
        'uom',
        'report_xlsx_helper',
    ],
    "data": [
        "views/res_partner_view.xml",
        "views/account_view.xml",
        "views/export_view.xml",
        "security/account_export_security.xml",
        "security/ir.model.access.csv",
    ],
}
