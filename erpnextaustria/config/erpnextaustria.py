from __future__ import unicode_literals
from frappe import _

def get_data():
    return[
        {
            "label": _("Taxes"),
            "icon": "fa fa-bank",
            "items": [
                {
                    "type": "doctype",
                    "name": "AT VAT Declaration",
                    "label": _("AT VAT Declaration"),
                    "description": _("AT VAT Declaration")
                },
                {
                    "type": "report",
                    "doctype": "Sales Invoice",
                    "name": "Summary Message",
                    "label": _("Summary Message"),
                    "description": _("Summary Message"),
                    "is_query_report": True
                },
                {
                    "type": "report",
                    "doctype": "Purchase Invoice",
                    "name": "Intrastat",
                    "label": _("Intrastat"),
                    "description": _("Intrastat"),
                    "is_query_report": True
                }
            ]
        },
        {
            "label": _("Settings"),
            "icon": "fa fa-wrench",
            "items": [
                   {
                       "type": "doctype",
                       "name": "ERPNextAustria Settings",
                       "label": _("ERPNextAustria Settings"),
                       "description": _("ERPNextAustria Settings")
                   }
            ]
        }
    ]
