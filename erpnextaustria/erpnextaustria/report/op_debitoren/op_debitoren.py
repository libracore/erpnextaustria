# Copyright (c) 2021, libracore and contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from erpnext.accounts.report.accounts_receivable.accounts_receivable import ReceivablePayableReport
from frappe import _

def execute(filters=None):
    args = {
        "party_type": "Customer",
        "naming_by": ["Selling Settings", "cust_master_name"],
    }
    columns, data, more, chart = ReceivablePayableReport(filters).run(args)
    columns = get_columns()
    # aggregate by customer
    output = []
    customers = []
    overall_totals = {
            'invoiced': 0,
            'outstanding': 0
        }
    for d in data:
        customer = d['party'] if 'party' in d else d['customer_name']
        if not customer in customers:
            customers.append(customer)
    for c in sorted(customers or []):
        customer_totals = {
            'invoiced': 0,
            'outstanding': 0
        }
        for d in data:
            customer = d['party'] if 'party' in d else d['customer_name']
            if customer == c:
                output.append(d)
                customer_totals['invoiced'] += d['invoiced']
                customer_totals['outstanding'] += d['outstanding']
                overall_totals['invoiced'] += d['invoiced']
                overall_totals['outstanding'] += d['outstanding']
        output.append({
            'party': c,
            'invoiced': customer_totals['invoiced'],
            'outstanding': customer_totals['outstanding']
        })
    # use manual total, automatic sum would be double the actual value
    output.append({
        'party': _("Total"),
        'invoiced': overall_totals['invoiced'],
        'outstanding': overall_totals['outstanding']
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
            "label": _("Customer"),
            "fieldname": "party",
            "fieldtype": "Link",
            "options": "Customer",
            "width": 120
        },
        {
            "label": _("Customer Name"),
            "fieldname": "customer_name",
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
