{
    "name": "SFTP Connector",
    "summary": "Framework for interacting with SFTP hosts",
    "version": "12.0.1.0.0",
    "category": "Base",
    "website": "https://druidoo.io",
    "author": "Druidoo",
    "license": "AGPL-3",
    "depends": ['connector_sftp', 'account_bank_statement_import_fr_cfonb'],
    "application": False,
    "installable": True,
    'data': [
        'security/ir.model.access.csv',
        'views/connector_sftp_fetchfile_view.xml',
        'data/data.xml',
    ],
}
