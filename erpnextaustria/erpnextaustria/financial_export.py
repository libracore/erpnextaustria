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
    acts_sheet_file = create_account_sheet_file(fiscal_year, company)
    journal_file = create_journal_file(fiscal_year, company)
    dbt_crt_balance_file = create_debtors_creditors_balance_file(fiscal_year, company)
    act_balance_file = create_account_balance_file(fiscal_year, company)
    
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

def create_account_sheet_file(fiscal_year, company):
    data = []
    # prepare debtors
    account_sheet = frappe.db.sql("""
            SELECT
                `name`,
                `posting_date`,
                `account`,
                `against`,
                `voucher_type`,
                `voucher_no`,
                `remarks`,
                `debit`,
                `credit`,
                `creation`
            FROM `tabGL Entry`
            WHERE
                `company` = "{company}"
                AND `posting_date` BETWEEN "{from_date}" AND "{to_date}"
            ORDER BY `account` ASC, `posting_date` ASC, `creation` ASC
        """.format(
            company=company, 
            from_date=frappe.get_value("Fiscal Year", fiscal_year, "year_start_date"), 
            to_date=frappe.get_value("Fiscal Year", fiscal_year, "year_end_date")
        ), as_dict=True)
    balances = {}
    for a in account_sheet:
        record = {
            'posting_date': a.posting_date,
            'account_number': (a.account or "").split(" ")[0],
            'against_number': (a.against or "").split(" ")[0],
            'voucher_type': (a.voucher_no or "").split("-")[0],
            'voucher_no': (a.voucher_no or ""),
            'remarks': make_safe_string(a.remarks),
            'debit': a.debit,
            'credit': (-1) * a.credit
        }
        
        # get tax
        if (a.voucher_type in ['Sales Invoice', 'Purchase Invoice']):
            doc = frappe.get_doc(a.voucher_type, a.voucher_no)
            tax_percent = None
            if doc.taxes and len(doc.taxes) > 0:
                tax_percent = doc.taxes[0].rate
                tax_amount = doc.taxes[0].base_tax_amount_after_discount_amount     # note: this is document, not account-level!
            
            record.update({
                'tax_percent': tax_percent,
                'tax_amount': ((a.debit - a.credit) * tax_percent/100) if tax_percent else None
            })
        
        if a.account not in balances:
            # derive opening account balance
            opening_balance = frappe.db.sql("""
                SELECT
                    IFNULL(SUM(`debit`) - SUM(`credit`), 0) AS `balance`
                FROM `tabGL Entry`
                WHERE
                    `company` = "{company}"
                    AND `account` = "{account}"
                    AND `posting_date` < "{start_date}"
                ;
            """.format(company=company, account=a.account, start_date=frappe.get_value("Fiscal Year", fiscal_year, "year_start_date")), as_dict=True)
            balances[a.account] = opening_balance[0]['balance']
        
        balances[a.account] += (a.debit - a.credit)
        record.update({'balance': balances[a.account]})
        
        data.append(record)
        
    # render template
    output_accounts = frappe.render_template("erpnextaustria/templates/xml/account_sheet_export.html", 
        {
            'fiscal_year': frappe.get_doc("Fiscal Year", fiscal_year),
            'company': company,
            'data': data
        }
    )
    
    # write file
    filename = "/tmp/ACL_Kontoblatt_{0}_{1}.csv".format(company, fiscal_year)
    f = open(filename, "w", encoding="utf-8")              # cp1252 would be required, but cannot encode all required chars
    f.write(output_accounts)
    f.close()
    return filename

def create_journal_file(fiscal_year, company):
    data = []
    # prepare debtors
    account_sheet = frappe.db.sql("""
            SELECT
                `name`,
                `posting_date`,
                `account`,
                `against`,
                `voucher_type`,
                `voucher_no`,
                `remarks`,
                `debit`,
                `credit`,
                `creation`
            FROM `tabGL Entry`
            WHERE
                `company` = "{company}"
                AND `posting_date` BETWEEN "{from_date}" AND "{to_date}"
            ORDER BY `name` ASC
        """.format(
            company=company, 
            from_date=frappe.get_value("Fiscal Year", fiscal_year, "year_start_date"), 
            to_date=frappe.get_value("Fiscal Year", fiscal_year, "year_end_date")
        ), as_dict=True)

    for a in account_sheet:
        record = {
            'name': a.name,
            'posting_date': a.posting_date,
            'account_number': (a.account or "").split(" ")[0],
            'against_number': (a.against or "").split(" ")[0],
            'voucher_type': (a.voucher_no or "").split("-")[0],
            'voucher_no': (a.voucher_no or ""),
            'remarks': make_safe_string(a.remarks),
            'debit': a.debit,
            'credit': (-1) * a.credit
        }
        
        # get tax
        if (a.voucher_type in ['Sales Invoice', 'Purchase Invoice']):
            doc = frappe.get_doc(a.voucher_type, a.voucher_no)
            tax_percent = None
            if doc.taxes and len(doc.taxes) > 0:
                tax_percent = doc.taxes[0].rate
                tax_amount = doc.taxes[0].base_tax_amount_after_discount_amount     # note: this is document, not account-level!
            
            record.update({
                'tax_percent': tax_percent,
                'tax_amount': ((a.debit - a.credit) * tax_percent/100) if tax_percent else None
            })
        
        data.append(record)
        
    # render template
    output_accounts = frappe.render_template("erpnextaustria/templates/xml/journal_export.html", 
        {
            'fiscal_year': frappe.get_doc("Fiscal Year", fiscal_year),
            'company': company,
            'data': data
        }
    )
    
    # write file
    filename = "/tmp/ACL_Journal_{0}_{1}.csv".format(company, fiscal_year)
    f = open(filename, "w", encoding="utf-8")              # cp1252 would be required, but cannot encode all required chars
    f.write(output_accounts)
    f.close()
    return filename
    
def create_debtors_creditors_balance_file(fiscal_year, company):
    data = []
    # prepare debtors
    debtors = frappe.get_all("Customer", fields=['name', 'customer_name', 'tax_id', 'payment_terms'])
    for d in debtors:
        balance = get_party_balances(d.name, company, fiscal_year)
        opening_balance = balance['opening_debit'] - balance['opening_credit']
        period_change = balance['total_debit'] - balance['total_credit']
        record = {
            'account': make_safe_string(d.name),
            'name': make_safe_string(d.customer_name),
            'opening_balance': opening_balance,
            'total_debit': balance['opening_debit'],
            'total_crdit': (-1) * balance['opening_credit'],
            'balance_debit': opening_balance + period_change if period_change >= 0 else None,
            'balance_credit': opening_balance + period_change if period_change < 0 else None,
        }
            
        data.append(record)
    
    # prepare creditors
    creditors = frappe.get_all("Supplier", fields=['name', 'supplier_name', 'tax_id', 'payment_terms'])
    for c in creditors:
        balance = get_party_balances(c.name, company, fiscal_year)
        opening_balance = balance['opening_debit'] - balance['opening_credit']
        period_change = balance['total_debit'] - balance['total_credit']
        record = {
            'account': make_safe_string(c.name),
            'name': make_safe_string(c.customer_name),
            'opening_balance': opening_balance,
            'total_debit': balance['opening_debit'],
            'total_crdit': (-1) * balance['opening_credit'],
            'balance_debit': opening_balance + period_change if period_change >= 0 else None,
            'balance_credit': opening_balance + period_change if period_change < 0 else None,
        }
            
        data.append(record)
        
    # render template
    output_debtors_creditors = frappe.render_template("erpnextaustria/templates/xml/debtors_creditors_balance_export.html", 
        {
            'fiscal_year': frappe.get_doc("Fiscal Year", fiscal_year),
            'company': company,
            'data': data
        }
    )
    
    # write file
    filename = "/tmp/ACL_Personensaldenliste_{0}_{1}.csv".format(company, fiscal_year)
    f = open(filename, "w", encoding="utf-8")              # cp1252 would be required, but cannot encode all required chars
    f.write(output_debtors_creditors)
    f.close()
    return filename


def create_account_balance_file(fiscal_year, company):
    data = []
    # prepare debtors
    accounts = frappe.get_all("Account", 
        filters={'company': company},
        fields=['name', 'account_name', 'account_number', 'root_type', 'account_type'],
        order_by='account_number')
    for a in accounts:
        if a.account_number:                            # only export with account numbers (leave structural elements)
            balance = get_party_balances(a.name, company, fiscal_year)
            opening_balance = balance['opening_debit'] - balance['opening_credit']
            period_change = balance['total_debit'] - balance['total_credit']
            record = {
                'account': make_safe_string(a.account_number),
                'name': make_safe_string(a.account_name),
                'opening_balance': opening_balance,
                'total_debit': balance['opening_debit'],
                'total_crdit': (-1) * balance['opening_credit'],
                'balance_debit': opening_balance + period_change if period_change >= 0 else None,
                'balance_credit': opening_balance + period_change if period_change < 0 else None,
            }
            data.append(record)
        
    # render template
    output_debtors_creditors = frappe.render_template("erpnextaustria/templates/xml/account_balance_export.html", 
        {
            'fiscal_year': frappe.get_doc("Fiscal Year", fiscal_year),
            'company': company,
            'data': data
        }
    )
    
    # write file
    filename = "/tmp/ACL_Saldenliste_{0}_{1}.csv".format(company, fiscal_year)
    f = open(filename, "w", encoding="utf-8")              # cp1252 would be required, but cannot encode all required chars
    f.write(output_debtors_creditors)
    f.close()
    return filename
    
def get_party_balances(party, company, fiscal_year):
    opening_party_balance = frappe.db.sql("""
            SELECT
                `account`,
                `against`,
                IFNULL(SUM(`debit`), 0) AS `total_debit`,
                IFNULL(SUM(`credit`), 0)  AS `total_credit`
            FROM `tabGL Entry`
            WHERE
                `company` = "{company}"
                AND `posting_date` < "{from_date}"
                AND `against` = "{party}";
        """.format(
            company=company, 
            from_date=frappe.get_value("Fiscal Year", fiscal_year, "year_start_date"), 
            to_date=frappe.get_value("Fiscal Year", fiscal_year, "year_end_date"),
            party=party
        ), as_dict=True)
        
    party_balance = frappe.db.sql("""
            SELECT
                `account`,
                `against`,
                IFNULL(SUM(`debit`), 0) AS `total_debit`,
                IFNULL(SUM(`credit`), 0)  AS `total_credit`
            FROM `tabGL Entry`
            WHERE
                `company` = "{company}"
                AND `posting_date` BETWEEN "{from_date}" AND "{to_date}"
                AND `against` = "{party}";
        """.format(
            company=company, 
            from_date=frappe.get_value("Fiscal Year", fiscal_year, "year_start_date"), 
            to_date=frappe.get_value("Fiscal Year", fiscal_year, "year_end_date"),
            party=party
        ), as_dict=True)
        
    return {
        'opening_debit': opening_party_balance[0]['total_debit'],
        'opening_credit': opening_party_balance[0]['total_credit'],
        'total_debit': party_balance[0]['total_debit'],
        'total_credit': party_balance[0]['total_credit'],
    }

def get_account_balances(account, company, fiscal_year):
    opening_party_balance = frappe.db.sql("""
            SELECT
                `account`,
                IFNULL(SUM(`debit`), 0) AS `total_debit`,
                IFNULL(SUM(`credit`), 0)  AS `total_credit`
            FROM `tabGL Entry`
            WHERE
                `company` = "{company}"
                AND `posting_date` < "{from_date}"
                AND `account` = "{account}";
        """.format(
            company=company, 
            from_date=frappe.get_value("Fiscal Year", fiscal_year, "year_start_date"), 
            to_date=frappe.get_value("Fiscal Year", fiscal_year, "year_end_date"),
            account=account
        ), as_dict=True)
        
    party_balance = frappe.db.sql("""
            SELECT
                `account`,
                `against`,
                IFNULL(SUM(`debit`), 0) AS `total_debit`,
                IFNULL(SUM(`credit`), 0)  AS `total_credit`
            FROM `tabGL Entry`
            WHERE
                `company` = "{company}"
                AND `posting_date` BETWEEN "{from_date}" AND "{to_date}"
                AND `account` = "{account}";
        """.format(
            company=company, 
            from_date=frappe.get_value("Fiscal Year", fiscal_year, "year_start_date"), 
            to_date=frappe.get_value("Fiscal Year", fiscal_year, "year_end_date"),
            account=account
        ), as_dict=True)
        
    return {
        'opening_debit': opening_party_balance[0]['total_debit'],
        'opening_credit': opening_party_balance[0]['total_credit'],
        'total_debit': party_balance[0]['total_debit'],
        'total_credit': party_balance[0]['total_credit'],
    }

def make_safe_string(s):
    return (s or "").replace(";", " ").replace("\n", " ").replace("\r", " ").replace("\"", "")
