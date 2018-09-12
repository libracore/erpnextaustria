# Copyright (c) 2017-2018, libracore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from datetime import datetime

def execute(filters=None):
    columns, data = [], []

    # prepare columns
    columns = [
        "Item:Link/Item:150", 
        "KN8 Code::100", 
        "Vers. Land::100", 
        "Ursp. Land::100", 
        "Eigenmasse KG::100",
        "Bes. Masseneinheit::100",
        "Rechn. Betrag::100",
        "Stat. Wert::100"
    ]

    # prepare filters
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
        
    # prepare query
    sql_query = """SELECT 
          `tabPurchase Invoice Item`.`item_code`,
          `tabItem`.`customs_tariff_number` AS `KN8 Code`,
          (SELECT `code` FROM `tabCountry` WHERE `tabCountry`.`name` = 
           (SELECT `country` FROM `tabAddress` WHERE `tabAddress`.`name` = `tabPurchase Invoice`.`supplier_address`)
          ) AS `Vers. Land`,
          (SELECT `code` FROM `tabCountry` WHERE `tabCountry`.`name` = `tabItem`.`country_of_origin`) AS `Ursp. Land`,
          `tabPurchase Invoice Item`.`total_weight` AS `Eigenmasse KG`,
          `tabPurchase Invoice Item`.`qty` AS `Bes. Masseneinheit`,
          FLOOR(`tabPurchase Invoice Item`.`base_net_amount`) AS `amount`,
          FLOOR(`tabPurchase Invoice Item`.`base_net_amount`) AS `value`
        FROM `tabPurchase Invoice Item`
        LEFT JOIN `tabPurchase Invoice` ON `tabPurchase Invoice Item`.`parent` = `tabPurchase Invoice`.`name`
        LEFT JOIN `tabItem` ON `tabPurchase Invoice Item`.`item_code` = `tabItem`.`item_code`
        WHERE `tabPurchase Invoice`.`docstatus` = 1
          AND `tabPurchase Invoice`.`taxes_and_charges` LIKE '%070%'
          AND `tabPurchase Invoice`.`posting_date` >= '{year}-{month}-01'
          AND `tabPurchase Invoice`.`posting_date` < '{year2}-{month2}-01'
        ;""".format(year=year, month=month, year2=year2, month2=month2)

    # run query, as list, otherwise export to Excel fails 
    data = frappe.db.sql(sql_query, as_list = True)

    return columns, data

