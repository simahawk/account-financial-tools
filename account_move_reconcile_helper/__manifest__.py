# -*- coding: utf-8 -*-
# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Account Move Reconcile Helper',
    'summary': """
        Provides tools to facilitate reconciliation""",
    'version': '10.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'ACSONE SA/NV, Odoo Community Association (OCA)',
    'website': 'https://www.acsone.eu',
    'depends': [
        'account_balance_line',
    ],
    'data': [
        'views/account_move_line.xml',
    ],
    'demo': [
    ],
}
