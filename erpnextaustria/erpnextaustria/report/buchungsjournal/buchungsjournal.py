# Copyright (c) 2017-2022, libracore (https://www.libracore.com) and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

def execute(filters=None):
    columns = get_columns(filters)
    data = get_data(filters)
    return columns, data

def get_columns(filters):
    return [
        {"label": _("Date"), "fieldname": "date", "fieldtype": "Link", "options": "Item", "width": 100},
        {"label": _("Account"), "fieldname": "account", "fieldtype": "Data", "width": 80},
        {"label": _("Debit"), "fieldname": "debit", "fieldtype": "Currency", "width": 120},
        {"label": _("Credit"), "fieldname": "credit", "fieldtype": "Currency", "width": 120},
        #{"label": _("Balance"), "fieldname": "balance", "fieldtype": "Currency", "width": 120},
        {"label": _("Against"), "fieldname": "against", "fieldtype": "Data", "width": 100},
        {"label": _("Party"), "fieldname": "party_name", "fieldtype": "Data", "width": 120},
        {"label": _("Remarks"), "fieldname": "remarks", "fieldtype": "Data", "width": 200},
        # {"label": _("Voucher type"), "fieldname": "voucher_type", "fieldtype": "Data", "width": 100},
        {"label": _("Voucher"), "fieldname": "voucher", "fieldtype": "Dynamic Link", "options": "voucher_type", "width": 120},
        {"label": _("Comment"), "fieldname": "comment", "fieldtype": "Data", "width": 200},
        {"label": _(""), "fieldname": "blank", "fieldtype": "Data", "width": 20}
    ]

def get_data(filters):
   
    data = []

    # get positions
    positions = frappe.db.sql("""SELECT 
            `tabGL Entry`.`posting_date` AS `posting_date`,
            `tabGL Entry`.`account` AS `account`,
            `tabGL Entry`.`debit` AS `debit`,
            `tabGL Entry`.`credit` AS `credit`,
            `tabGL Entry`.`remarks` AS `remarks`,
            `tabGL Entry`.`voucher_type` AS `voucher_type`,
            `tabGL Entry`.`voucher_no` AS `voucher`,
            `tabGL Entry`.`against` AS `against`,
            IFNULL(`tabCustomer`.`customer_name`, IFNULL(`tabSupplier`.`supplier_name`, "")) AS `party_name`,
            (SELECT `tabComment`.`content` 
             FROM `tabComment`
             WHERE 
                `tabComment`.`reference_name` = `tabGL Entry`.`voucher_no`
                AND `tabComment`.`reference_doctype` = `tabGL Entry`.`voucher_type`
             ORDER BY `tabComment`.`creation` DESC
             LIMIT 1) AS `comment`
        FROM `tabGL Entry`
        LEFT JOIN `tabCustomer` ON `tabCustomer`.`name` = `tabGL Entry`.`against`
        LEFT JOIN `tabSupplier` ON `tabSupplier`.`name` = `tabGL Entry`.`against`
        WHERE
          `tabGL Entry`.`docstatus` = 1
          AND DATE(`tabGL Entry`.`posting_date`) >= "{from_date}"
          AND DATE(`tabGL Entry`.`posting_date`) <= "{to_date}"
        ORDER BY `tabGL Entry`.`posting_date` ASC;""".format(from_date=filters.from_date, to_date=filters.to_date), as_dict=True)

    for position in positions:

        if "," in (position['against'] or ""):
            against = "{0} (...)".format((position['against'] or "").split(" ")[0])
        else:
            against = (position['against'] or "").split(" ")[0]
        if len(position['remarks'] or "") > 30:
            remarks = "{0}...".format(position['remarks'][:30])
        else:
            remarks = position['remarks']
        data.append({
            'date': position['posting_date'], 
            'account': position['account'][0:4],
            'debit': position['debit'],
            'credit': position['credit'],
            'voucher_type': position['voucher_type'],
            'voucher': position['voucher'],
            'against': against,
            'remarks': remarks,
            'party_name': position['party_name'],
            'comment': position['comment']
        })

    return data
