{
    "name": "Cron Job to import cfonb files",
    "summary": "Cron Job to import cfonb files",
    "version": "12.0.1.0.0",
    "category": "Base",
    "website": "https://druidoo.io",
    "author": "Druidoo",
    "license": "AGPL-3",
    "depends": ['connector_sftp_fetchfile'],
    "application": False,
    "installable": True,
    'data': [
        'data/data.xml',
    ],
}
