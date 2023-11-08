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
        "views/product_view.xml",
        "views/product_pricelist_view.xml",
        "views/purchase_view.xml",
        "views/sale_view.xml",
        "views/stock_view.xml",
        "views/res_partner_view.xml",
        "views/account_move_view.xml",
        "views/is_export_compta.xml",
        "views/menu.xml",
        "report/conditions_generales_de_vente_templates.xml",
        "report/is_sale_order_colis_report.xml",
        "report/sale_report_templates.xml",
        "report/report_deliveryslip.xml",
        "report/report_stockpicking_operations.xml",
        "report/report.xml",
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

