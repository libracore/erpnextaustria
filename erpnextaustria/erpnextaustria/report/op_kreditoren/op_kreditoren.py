# Copyright (c) 2021, libracore and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from erpnext.accounts.report.accounts_receivable.accounts_receivable import ReceivablePayableReport
from frappe import _
def execute(filters=None):
    args = {
        "party_type": "Supplier",
        "naming_by": ["Buying Settings", "supp_master_name"],
    }
    columns, data, more, chart = ReceivablePayableReport(filters).run(args)
    columns = get_columns()
    # aggregate by supplier
    output = []
    suppliers = []
    for d in data:
        supplier = d['party'] if 'party' in d else d['supplier_name']
        if not supplier in suppliers:
            suppliers.append(supplier)
    for c in sorted(suppliers or []):
        supplier_totals = {
            'invoiced': 0,
            'outstanding': 0
        }
        for d in data:
            supplier = d['party'] if 'party' in d else d['supplier_name']
            if supplier == c:
                output.append(d)
                supplier_totals['invoiced'] += d['invoiced']
                supplier_totals['outstanding'] += d['outstanding']
        output.append({
            'party': c,
            'invoiced': supplier_totals['invoiced'],
            'outstanding': supplier_totals['outstanding']
        })
    return columns, output

def get_columns():
    columns = [
        {
            "label": _("Posting Date"),
            "fieldname": "posting_date",
            "fieldtype": "Date",
            "width": 120
        },
        {
            "label": _("Due Date"),
            "fieldname": "due_date",
            "fieldtype": "Date",
            "width": 120
        },
        {
            "label": _("Supplier"),
            "fieldname": "party",
            "fieldtype": "Link",
            "options": "Supplier",
            "width": 120
        },
        {
            "label": _("Supplier Name"),
            "fieldname": "supplier_name",
            "fieldtype": "Data",
            "width": 120
        },
        {
            "label": _("Voucher Type"),
            "fieldname": "voucher_type",
            "fieldtype": "Data",
            "width": 120
        },
        {
            "label": _("Voucher No"),
            "fieldname": "voucher_no",
            "fieldtype": "Dynamic Link",
            "options": "voucher_type",
            "width": 120
        },
        {
            "label": _("Invoiced"),
            "fieldname": "invoiced",
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "label": _("Outstanding"),
            "fieldname": "outstanding",
            "fieldtype": "Currency",
            "width": 120
        }
    ]
    return columns

