# -*- coding: utf-8 -*-
# Copyright (c) 2017-2018, libracore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from datetime import datetime

def execute(filters=None):
    columns, data = [], []

    # prepare columns
    columns = [
        "Country::100", 
        "Tax ID::150", 
        "Revenue::150", 
        "Code::100"
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
        
    data = get_data(month, year)

    return columns, data

def get_data(month, year):
    # prepare timeframe
    month2 = month + 1
    if month2 > 12:
        month2 = month2 - 12
        year2 = year + 1
    else:
        year2 = year
    
    # prepare query
    sql_query = """SELECT 
          SUBSTRING(`tabCustomer`.`tax_id`, 1, 2) AS `country`,
          `tabCustomer`.`tax_id` AS `tax_id`, 
          FLOOR(SUM(`tabSales Invoice Item`.`base_net_amount`)) AS `amount`,
          /*`tabSales Invoice Item`.`base_net_amount`,*/
          /*`tabSales Invoice`.`name`, */
          /*`tabSales Invoice Item`.`item_code`,*/
          IF(`tabItem`.`is_stock_item` = 1, "", "1") AS `code`
          /* CONCAT(`tabCustomer`.`tax_id`, ":", `tabItem`.`is_stock_item`) AS `position` */
        FROM `tabSales Invoice Item`
        LEFT JOIN `tabSales Invoice` ON `tabSales Invoice Item`.`parent` = `tabSales Invoice`.`name`
        LEFT JOIN `tabCustomer` ON `tabSales Invoice`.`customer` = `tabCustomer`.`name`
        LEFT JOIN `tabItem` ON `tabSales Invoice Item`.`item_code` = `tabItem`.`item_code`
        WHERE 
          `tabSales Invoice`.`docstatus` = 1
          AND `tabSales Invoice`.`posting_date` >= '{year}-{month}-01'
          AND `tabSales Invoice`.`posting_date` < '{year2}-{month2}-01'
          AND `tabCustomer`.`steuerregion` = "EU"
        GROUP BY (CONCAT(`tabCustomer`.`tax_id`, ":", `tabItem`.`is_stock_item`));""".format(
            year=year, month=month, year2=year2, month2=month2)

    # run query, as list, otherwise export to Excel fails 
    data = frappe.db.sql(sql_query, as_list = True)
    return data
    
@frappe.whitelist()
def generate_transfer_file(month, year):
    #try:        
    # fetch data
    data = get_data(int(month), int(year))
    # create xml header
    content = make_line("<?xml version=\"1.0\" encoding=\"UTF-8\"?>")
    # define xml root node
    content += make_line("<ERKLAERUNGS_UEBERMITTLUNG>")
    content += make_line(" <INFO_DATEN>")
    content += make_line("  <ART_IDENTIFIKATIONSBEGRIFF>FASTNR</ART_IDENTIFIKATIONSBEGRIFF>")
    fastnr = frappe.get_value("ERPNextAustria Settings", "ERPNextAustria Settings", "fastnr")
    companies = frappe.get_all("Company", fields=['name'])
    company = companies[0]['name']
    content += make_line("  <IDENTIFIKATIONSBEGRIFF>{0}</IDENTIFIKATIONSBEGRIFF>".format(fastnr))
    content += make_line("  <PAKET_NR>1</PAKET_NR>")
    now = datetime.now()
    content += make_line("  <DATUM_ERSTELLUNG type=\"datum\">{0:04d}-{1:02d}-{2:02d}</DATUM_ERSTELLUNG>".format(now.year, now.month, now.day))
    content += make_line("  <UHRZEIT_ERSTELLUNG type=\"uhrzeit\">{0:02d}:{1:02d}:{2:02d}</UHRZEIT_ERSTELLUNG>".format(now.hour, now.minute, now.second))
    content += make_line("  <ANZAHL_ERKLAERUNGEN>1</ANZAHL_ERKLAERUNGEN>")
    content += make_line(" </INFO_DATEN>")
    content += make_line(" <ERKLAERUNG art=\"U13\">")
    content += make_line("  <SATZNR>1</SATZNR>")
    content += make_line("  <ALLGEMEINE_DATEN>")
    content += make_line("   <ANBRINGEN>U13</ANBRINGEN>")
    content += make_line("   <ZRVON type=\"jahrmonat\">{0:04d}-{1:02d}</ZRVON>".format(year, month))
    content += make_line("   <ZRBIS type=\"jahrmonat\">{0:04d}-{1:02d}</ZRBIS>".format(year, month))
    content += make_line("   <FASTNR>{0}</FASTNR>".format(fastnr))
    content += make_line("   <KUNDENINFO>{0}</KUNDENINFO>".format(company))
    content += make_line("  </ALLGEMEINE_DATEN>")
    for i in range(0, len(data)):
        content += make_line("  <ZM>")
        content += make_line("  <UID_MS>{0}</UID_MS>".format(data[i][1]))
        content += make_line("  <SUM_BGL type=\"kz\">{0}</SUM_BGL>".format(data[i][2]))
        content += make_line("  <SOLEI>{0}</SOLEI>".format(data[i][3]))
        content += make_line("  </ZM>")
    content += make_line(" </ERKLAERUNG>")
    content += make_line("</ERKLAERUNGS_UEBERMITTLUNG>")
 
    return { 'content': content }
    #except IndexError:
    #    frappe.msgprint( _("Please select at least one payment."), _("Information") )
    #    return
    #except:
    #    frappe.throw( _("Error while generating xml. Make sure that you made required customisations to the DocTypes.") )
    #    return

# adds Windows-compatible line endings (to make the xml look nice)    
def make_line(line):
    return line + "\r\n"
