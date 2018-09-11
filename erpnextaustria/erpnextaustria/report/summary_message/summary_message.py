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
		  IF(`tabItem`.`is_stock_item` = 1, "1", "") AS `code`
		  /* CONCAT(`tabCustomer`.`tax_id`, ":", `tabItem`.`is_stock_item`) AS `position` */
		FROM `tabSales Invoice Item`
		LEFT JOIN `tabSales Invoice` ON `tabSales Invoice Item`.`parent` = `tabSales Invoice`.`name`
		LEFT JOIN `tabCustomer` ON `tabSales Invoice`.`customer` = `tabCustomer`.`name`
		LEFT JOIN `tabItem` ON `tabSales Invoice Item`.`item_code` = `tabItem`.`item_code`
		WHERE 
		  `tabSales Invoice`.`docstatus` = 1
		  AND `tabSales Invoice`.`posting_date` >= '{year}-{month}-01'
		  AND `tabSales Invoice`.`posting_date` < '{year2}-{month2}-01'
		GROUP BY (CONCAT(`tabCustomer`.`tax_id`, ":", `tabItem`.`is_stock_item`));""".format(
			year=year, month=month, year2=year2, month2=month2)

	# run query, as list, otherwise export to Excel fails 
	data = frappe.db.sql(sql_query, as_list = True)

	return columns, data

