# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Account Export',
    "summary": "Export account move lines for accounting software",
    'version': '1.0',
    "description": """Provides generic functionality to export account moves
    as csv files that will be imported in accounting software
    """,
    "category": 'Accounting & Finance',
    "author": "Druidoo",
    'website': 'http://www.druidoo.io',
    "license": "AGPL-3",
    "depends": ['base', 'account', 'document', 'mail', 'uom'],
    "data": [
        "views/res_partner_view.xml",
        "views/account_view.xml",
        "views/export_view.xml",
        "security/account_export_security.xml",
        "security/ir.model.access.csv",
    ],
}
