# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'French ECO Participation Taxes',
    'version': '1.0',
    'category': 'Accounting',
    'summary': """
Provides French ECO Participation Taxes
    """,
    'author': 'Druidoo',
    'website': 'https://druidoo.io/',
    'depends': [
        'l10n_fr',
        'account_tax_weight',
    ],
    'data': [
        'data/account.account.template.csv',
        'data/account_tax_data.xml',
        'data/post_object_data.xml',
    ],

    'test': [],
    'demo': [],
    'installable': True,
    'active': False,
    'application': False,
}
