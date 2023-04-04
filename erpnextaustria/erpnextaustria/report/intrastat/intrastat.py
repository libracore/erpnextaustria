# -*- coding: utf-8 -*-
# Copyright (c) 2017-2023, libracore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from datetime import datetime
from frappe.utils import cint
from frappe import _

def execute(filters=None):
    columns, data = [], []

    # prepare columns
    columns = [
        {'fieldname': 'kn8', 'label': _("KN8-Code"), 'fieldtype': 'Data', 'width': 100}, 
        {'fieldname': 'item_name', 'label': _("Item"), 'fieldtype': 'Data',  'width': 150}, 
        {'fieldname': 'vers_land', 'label': _("Vers. Land"), 'fieldtype': 'Data', 'width': 80}, 
        {'fieldname': 'ursp_land', 'label': _("Ursp. Land"), 'fieldtype': 'Data', 'width': 80}, 
        {'fieldname': 'eigenmasse_kg', 'label': _("Eigenmasse KG"), 'fieldtype': 'Data', 'width': 100}, 
        {'fieldname': 'bess_mass', 'label': _("Bes. Masseneinheit"), 'fieldtype': 'Data', 'width': 100}, 
        {'fieldname': 'amount', 'label': _("Rechn. Betrag"), 'fieldtype': 'Data', 'width': 100}, 
        {'fieldname': 'value', 'label': _("Stat. Wert"), 'fieldtype': 'Data', 'width': 100}, 
        {'fieldname': 'uid', 'label': _("EmpfängerUID"), 'fieldtype': 'Data', 'width': 100},
        {'fieldname': 'dn', 'label': _("Reference"), 'fieldtype': 'Dynamic Link', 'options': 'dt', 'width': 100}
    ]

    # prepare filters
    today = datetime.today()
    if filters.month:
        month = filters.month
    else:
        month = today.month;
    if filters.year:
        year = filters.year
    else:
        year = today.year;
    # prepare timeframe
    month2 = month + 1
    if month2 > 12:
        month2 = month2 - 12
        year2 = year + 1
    else:
        year2 = year
        
    data = get_data(month, year, filters.mode, filters.aggregate)

    return columns, data

def get_data(month, year, mode, aggregate=0):
    # prepare timeframe
    month2 = month + 1
    if month2 > 12:
        month2 = month2 - 12
        year2 = year + 1
    else:
        year2 = year
    
    # prepare query
    if mode == "In":
        if cint(aggregate) == 1:
            group_by = " GROUP BY `tabPurchase Invoice`.`name` "
        else:
            group_by = " GROUP BY `tabPurchase Invoice Item`.`name` "
        sql_query = """SELECT 
              `tabPurchase Invoice Item`.`item_code`,
              `tabPurchase Invoice Item`.`item_name`,
              `tabItem`.`customs_tariff_number` AS `kn8`,
              (SELECT UPPER(`code`) FROM `tabCountry` WHERE `tabCountry`.`name` = 
               (SELECT `country` FROM `tabAddress` WHERE `tabAddress`.`name` = `tabPurchase Invoice`.`supplier_address`)
              ) AS `vers_land`,
              (SELECT UPPER(`code`) FROM `tabCountry` WHERE `tabCountry`.`name` = `tabItem`.`country_of_origin`) AS `ursp_land`,
              (IF (`tabPurchase Invoice Item`.`weight_uom` = "g", 
                FLOOR(`tabPurchase Invoice Item`.`total_weight` / 1000),
                `tabPurchase Invoice Item`.`total_weight`)) AS `eigenmasse_kg`,
              FLOOR(SUM(`tabPurchase Invoice Item`.`qty`)) AS `bess_mass`,
              FLOOR(SUM(`tabPurchase Invoice Item`.`base_net_amount`)) AS `amount`,
              FLOOR(SUM(`tabPurchase Invoice Item`.`base_net_amount`)) AS `value`,
              `tabCompany`.`tax_id` AS `uid`,
              "Purchase Invoice" AS `dt`,
              `tabPurchase Invoice`.`name` AS `dn`
            FROM `tabPurchase Invoice Item`
            LEFT JOIN `tabPurchase Invoice` ON `tabPurchase Invoice Item`.`parent` = `tabPurchase Invoice`.`name`
            LEFT JOIN `tabItem` ON `tabPurchase Invoice Item`.`item_code` = `tabItem`.`item_code`
            LEFT JOIN `tabCompany` ON `tabPurchase Invoice`.`company` = `tabCompany`.`name`
            WHERE `tabPurchase Invoice`.`docstatus` = 1
              AND `tabPurchase Invoice`.`taxes_and_charges` LIKE '%070%'
              AND `tabPurchase Invoice`.`posting_date` >= '{year}-{month}-01'
              AND `tabPurchase Invoice`.`posting_date` < '{year2}-{month2}-01'
            {group_by}
            ;""".format(year=year, month=month, year2=year2, month2=month2, group_by=group_by)
    else:
        if cint(aggregate) == 1:
            group_by = " GROUP BY `tabSales Invoice`.`name` "
        else:
            group_by = " GROUP BY `tabSales Invoice Item`.`name` "
        sql_query = """SELECT 
              `tabSales Invoice Item`.`item_code`,
              `tabSales Invoice Item`.`item_name`,
              `tabItem`.`customs_tariff_number` AS `kn8`,
              (SELECT UPPER(`code`) FROM `tabCountry` WHERE `tabCountry`.`name` = 
               (SELECT `country` FROM `tabAddress` WHERE `tabAddress`.`name` = `tabSales Invoice`.`customer_address`)
              ) AS `vers_land`,
              (SELECT UPPER(`code`) FROM `tabCountry` WHERE `tabCountry`.`name` = `tabItem`.`country_of_origin`) AS `ursp_land`,
              (IF (`tabSales Invoice Item`.`weight_uom` = "g", 
                FLOOR(`tabSales Invoice Item`.`total_weight` / 1000),
                `tabSales Invoice Item`.`total_weight`)) AS `eigenmasse_kg`,
              FLOOR(SUM(`tabSales Invoice Item`.`qty`)) AS `bess_mass`,
              FLOOR(IF(SUM(`tabSales Invoice Item`.`base_net_amount`) = 0, SUM(`tabSales Invoice Item`.`base_amount`), SUM(`tabSales Invoice Item`.`base_net_amount`))) AS `amount`,
              FLOOR(IF(SUM(`tabSales Invoice Item`.`base_net_amount`) = 0, SUM(`tabSales Invoice Item`.`base_amount`), SUM(`tabSales Invoice Item`.`base_net_amount`))) AS `value`,
              `tabSales Invoice`.`tax_id` AS `uid`,
              "Sales Invoice" AS `dt`,
              `tabSales Invoice`.`name` AS `dn`
            FROM `tabSales Invoice Item`
            LEFT JOIN `tabSales Invoice` ON `tabSales Invoice Item`.`parent` = `tabSales Invoice`.`name`
            LEFT JOIN `tabItem` ON `tabSales Invoice Item`.`item_code` = `tabItem`.`item_code`
            WHERE `tabSales Invoice`.`docstatus` = 1
              AND `tabSales Invoice`.`taxes_and_charges` LIKE '%017%'
              AND `tabSales Invoice`.`posting_date` >= '{year}-{month}-01'
              AND `tabSales Invoice`.`posting_date` < '{year2}-{month2}-01'
            {group_by}
            ;""".format(year=year, month=month, year2=year2, month2=month2, group_by=group_by)
    # run query, as list, otherwise export to Excel fails 
    data = frappe.db.sql(sql_query, as_dict = True)
    return data

@frappe.whitelist()
def generate_transfer_file(month, year, mode, aggregate=0):    
    # fetch data
    data = get_data(int(month), int(year), mode, aggregate)
    
    # create csv header
    content = make_line("KN8-Code;Warenbezeichnung;Handelspartnerland;Ursprungsland;Art des Geschäftes;Eigenmasse;Besondere Maßeinheit;Rechnungsbetrag;Statistischer Wert;EmpfängerUID")
    for i in range(0, len(data)):
        if data[i]['kn8']:
            content += make_line("{kn8};{item_name};{supl_cntry};{source_cntry};{type};{uom};{spec_uom};{amount};{value};{uid}".format(
                type="11",
                kn8=(data[i]['kn8'] or '').replace(' ', ''),
                item_name=data[i]['item_name'],
                supl_cntry=data[i]['vers_land'],
                source_cntry=data[i]['ursp_land'],
                uom=("{:.3f}".format(data[i]['eigenmasse_kg'] or 0)).replace(".", ","),
                spec_uom=("{:.3f}".format(data[i]['bess_mass'] or 0)).replace(".", ","),
                amount=("{:.2f}".format(data[i]['amount'])).replace(".", ","),
                value=("{:.2f}".format(data[i]['value'])).replace(".", ","),
                uid=data[i]['uid']
            ))
 
    return { 'content': content }

# adds Windows-compatible line endings (to make the xml look nice)    
def make_line(line):
    return line + "\r\n"
