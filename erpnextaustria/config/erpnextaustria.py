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
                   }
            ]
        }
    ]
