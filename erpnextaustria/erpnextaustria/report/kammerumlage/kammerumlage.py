# Copyright (c) 2013, libracore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
import ast          # to parse str to dict (from JS calls)
from datetime import datetime

def execute(filters=None):
    if type(filters) is str:
        filters = ast.literal_eval(filters)
    else:
        filters = dict(filters)
    columns = get_columns(filters)
    data = get_data(filters)
    return columns, data

def get_columns(filters):
    columns = [
        {"label": _("Account"), "fieldname": "account", "fieldtype": "Link", "options": "Item", "width": 150}
    ]
    months = {
        'Q1': [_("January"), _("February"), _("March")],
        'Q2': [_("April"), _("May"), _("June")],
        'Q3': [_("July"), _("August"), _("September")],
        'Q4': [_("October"), _("November"), _("December")]
    }
    for i in range(0, len(months[filters['quarter']])):
        columns.append({
            "label": "{0} {1}".format(months[filters['quarter']][i], filters['year']), 
            "fieldname": "m{0}".format(i), "fieldtype": "Currency", "width": 140
        })
        
    columns.append({
        "label": "{0} {1} {2}".format(_("Total"), filters['quarter'], filters['year']), 
        "fieldname": "total", "fieldtype": "Currency", "width": 100
    })
    columns.append({
        "label": "",  "fieldname": "blank", "fieldtype": "Data", "width": 20
    })
    return columns

@frappe.whitelist()
def get_data(filters):
    if filters['quarter'] == "Q1":
        months = ['01', '02', '03']
    elif filters['quarter'] == "Q2":
        months = ['04', '05', '06']
    elif filters['quarter'] == "Q3":
        months = ['07', '08', '09']
    elif filters['quarter'] == "Q4":
        months = ['10', '11', '12']
    
    data = frappe.db.sql("""SELECT `account`, `is_deduction`, `deduction` FROM `tabKammerumlage Account` ORDER BY `account` ASC;""", as_dict=True)
    
    for d in range(0, len(data)):
        for m in range(0, len(months)):
            if data[d]['is_deduction'] == 1:
                deduction = data[d]['deduction']
            else:
                deduction = 1
            sql_query = """SELECT 
                      {deduction} * IFNULL(SUM(`debit` - `credit`), 0) AS `amount`
                    FROM `tabGL Entry`
                    WHERE 
                      `tabGL Entry`.`account` = "{account}"
                      AND `tabGL Entry`.`company` = "{company}"
                      AND `tabGL Entry`.`posting_date` LIKE "{year}-{month}-%"
                    """.format(year=filters['year'], month=months[m], account=data[d]['account'], company=filters['company'], deduction=deduction)
            value = frappe.db.sql(sql_query, as_dict=True)
            data[d]["m{0}".format(m)] = value[0]['amount']
    
    # compute totals
    totals = {'m0': 0.0, 'm1': 0.0, 'm2': 0.0}
    for d in data:
        d['total'] = d['m0'] + d['m1'] + d['m2']
        totals['m0'] += d['m0']
        totals['m1'] += d['m1']
        totals['m2'] += d['m2']
    total = totals['m0'] + totals['m1'] +totals['m2']
    rate = frappe.get_value("ERPNextAustria Settings", "ERPNextAustria Settings", "ansatz_kammerumlage")
    fee = (float(rate or 0) / 100) * total
    data.append({
        'm0': totals['m0'],
        'm1': totals['m1'],
        'm2': totals['m2'],
        'total': total
    })
    data.append({
        'total': fee
    })
    
    return data

@frappe.whitelist()
def generate_transfer_file(filters):
    # collect values
    if type(filters) is str:
        filters = ast.literal_eval(filters)
    else:
        filters = dict(filters)
    if filters['quarter'] == "Q1":
        months = ['01', '03']
    elif filters['quarter'] == "Q2":
        months = ['04', '06']
    elif filters['quarter'] == "Q3":
        months = ['07', '09']
    elif filters['quarter'] == "Q4":
        months = ['10', '12']
    data = get_data(filters)
    settings = frappe.get_doc("ERPNextAustria Settings", "ERPNextAustria Settings")
    # compile into dataset
    doc = {
        'creation_date': datetime.now().strftime("%Y-%m-%d"),
        'creation_time': datetime.now().strftime("%H:%M:%S"),
        'fastnr': (settings.fastnr or "").replace(".", "").replace(" ", ""),
        'paket': 1,
        'month_from': "{year}-{month}".format(year=filters['year'], month=months[0]),
        'month_to': "{year}-{month}".format(year=filters['year'], month=months[1]),
        'amount': round(data[-1]['total'], 2)
    }
    # render into html
    content = frappe.render_template('erpnextaustria/erpnextaustria/report/kammerumlage/kammerumlage.html', doc)
    return {'content': content}
