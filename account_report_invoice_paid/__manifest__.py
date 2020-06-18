# Copyright (C) 2020-Today: Druidoo (<http://www.druidoo.io/>)
# @author: Druidoo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html

{
    'name': 'Account Invoice Report Paid',
    'summary': '',
    'version': '12.0.1.1.0',
    'category': 'Accounting',
    'author': 'Druidoo',
    'website': 'http://www.druidoo.io',
    'license': 'AGPL-3',
    'depends': [
        'account',
    ],
    'data': [
        'views/report_invoice_templates.xml',
    ],
    'application': False,
    'installable': True,
}
