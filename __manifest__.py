# -*- coding: utf-8 -*-
{
    'name'     : 'InfoSaône - Module Odoo 16 pour Jurabotec',
    'version'  : '0.1',
    'author'   : 'InfoSaône',
    'category' : 'InfoSaône',
    'description': """
InfoSaône - Module Odoo 16 pour Jurabotec
===================================================
""",
    'maintainer' : 'InfoSaône',
    'website'    : 'http://www.infosaone.com',
    'depends'    : [
        'base',
        "sale_management",
        "purchase",
        "account",
    ],
    'data' : [
        "security/ir.model.access.csv",
        "views/sale_view.xml",
        "views/stock_view.xml",
    ],
    'installable': True,
    'application': True,
    'qweb': [
    ],
   'assets': {
        'web.assets_backend': [
            'is_jurabotec/static/src/scss/styles.scss',
            'is_jurabotec/static/src/script.js',
            'is_jurabotec/static/src/templates.xml',
        ]
   },
    'license': 'LGPL-3',
}

