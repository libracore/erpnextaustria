# -*- coding: utf-8 -*-
# Copyright (c) 2018-2022, libracore and contributors
# For license information, please see license.txt
#
# This file contains the financial export logic for finance reviews
#

import frappe
from erpnextswiss.scripts.crm_tools import get_primary_customer_address, get_primary_supplier_address

ROOT_TYPES = {
    'Asset': "1",
    'Liability': "2",
    'Income': "4",
    'Expense': "3",
    'Equity': "2"
}

@frappe.whitelist()
def create_financial_export(fiscal_year, company):
    dbt_crt_file = create_debtors_creditors_file(fiscal_year, company)
    acts_file = create_accounts_file(fiscal_year, company)
    
    # create zip archie
    
    # remove tmp files
    
    return
    
    
def create_debtors_creditors_file(fiscal_year, company):
    data = []
    # prepare debtors
    debtors = frappe.get_all("Customer", fields=['name', 'customer_name', 'tax_id', 'payment_terms'])
    for d in debtors:
        record = {
            'account': make_safe_string(d.name),
            'name': make_safe_string(d.customer_name),
            'uid': make_safe_string(d.tax_id),
            'payment_terms': make_safe_string(d.payment_terms)
        }
        if d.payment_terms:
            record.update({
                'skonto_days_1': frappe.get_cached_value("Payment Terms Template", d.payment_terms, 'skonto_days'),
                'skonto_percent_1': frappe.get_cached_value("Payment Terms Template", d.payment_terms, 'skonto_percent')
            })
        address = get_primary_customer_address(d.name)
        if address:
            record.update({
                'street': make_safe_string(address.address_line1),
                'pincode': make_safe_string(address.pincode),
                'city': make_safe_string(address.city),
                'country': make_safe_string(address.country)
            })
            
        data.append(record)
    
    # prepare creditors
    creditors = frappe.get_all("Supplier", fields=['name', 'supplier_name', 'tax_id', 'payment_terms'])
    for c in creditors:
        record = {
            'account': make_safe_string(c.name),
            'name': make_safe_string(c.supplier_name),
            'uid': make_safe_string(c.tax_id),
            'payment_terms': make_safe_string(c.payment_terms)
        }
        if c.payment_terms:
            record.update({
                'skonto_days_1': frappe.get_cached_value("Payment Terms Template", c.payment_terms, 'skonto_days'),
                'skonto_percent_1': frappe.get_cached_value("Payment Terms Template", c.payment_terms, 'skonto_percent')
            })
        address = get_primary_supplier_address(c.name)
        if address:
            record.update({
                'street': make_safe_string(address.address_line1),
                'pincode': make_safe_string(address.pincode),
                'city': make_safe_string(address.city),
                'country': make_safe_string(address.country)
            })
            
        data.append(record)
        
    # render template
    output_debtors_creditors = frappe.render_template("erpnextaustria/templates/xml/debtors_creditors_export.html", 
        {
            'fiscal_year': frappe.get_doc("Fiscal Year", fiscal_year),
            'company': company,
            'data': data
        }
    )
    
    # write file
    filename = "/tmp/ACL_Personenkonten_{0}_{1}.csv".format(company, fiscal_year)
    f = open(filename, "w", encoding="utf-8")              # cp1252 would be required, but cannot encode all required chars
    f.write(output_debtors_creditors)
    f.close()
    return filename

def create_accounts_file(fiscal_year, company):
    data = []
    # prepare debtors
    accounts = frappe.get_all("Account", 
        filters={'company': company},
        fields=['name', 'account_name', 'account_number', 'root_type', 'account_type'],
        order_by='account_number')
    for a in accounts:
        if a.account_number:                            # only export with account numbers (leave structural elements)
            record = {
                'account': make_safe_string(a.account_number),
                'name': make_safe_string(a.account_name),
                'root_type': ROOT_TYPES[a.root_type],
                'account_type': make_safe_string(a.account_type)
            }
                
            data.append(record)
        
    # render template
    output_accounts = frappe.render_template("erpnextaustria/templates/xml/accounts_export.html", 
        {
            'fiscal_year': frappe.get_doc("Fiscal Year", fiscal_year),
            'company': company,
            'data': data
        }
    )
    
    # write file
    filename = "/tmp/ACL_Sachkonten_{0}_{1}.csv".format(company, fiscal_year)
    f = open(filename, "w", encoding="utf-8")              # cp1252 would be required, but cannot encode all required chars
    f.write(output_accounts)
    f.close()
    return filename
    
def make_safe_string(s):
    return (s or "").replace(";", " ").replace("\n", " ").replace("\r", " ").replace("\"", "")
