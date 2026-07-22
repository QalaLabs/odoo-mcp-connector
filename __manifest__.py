# -*- coding: utf-8 -*-
# Part of Qala Labs. See LICENSE file for full copyright and licensing details.
{
    'name': "Odoo MCP Connector",
    'version': '16.0.1.0.0',
    'category': "Extra Tools",
    'summary': "Connect AI Assistants (Claude, Cursor, Copilot) to Odoo 16 ERP using Model Context Protocol (MCP)",
    'description': """
        Odoo MCP Connector
        ==================
        This module enables seamless interaction between AI Assistants and your Odoo 16 ERP instance.
        
        Features:
        - Full Odoo Integration: CRM, Accounting, Sales, Purchase, Inventory, Expenses
        - Standard Odoo 16 API Support: XML-RPC and External APIs
        - Secure Authentication: Support for Scoped API Keys and User Credentials
        - Natural Language Commands: Search, create, update, and analyze ERP records
    """,
    'author': 'Qala Labs',
    'price': 0,
    'currency': 'EUR',
    'website': 'https://github.com/QalaLabs/odoo-mcp-connector',
    'depends': ['base', 'web'],
    'assets': {},
    'data': [],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
    'images': [],
}
