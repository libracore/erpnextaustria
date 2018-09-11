# -*- coding: utf-8 -*-
# Copyright (c) 2018, libracore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class ATVATDeclaration(Document):
    # generate xml export
    def generate_transfer_file(self):
        #try:        
        # create xml header
        content = make_line("<?xml version=\"1.0\" encoding=\"UTF-8\"?>")
        # define xml root node
        content += make_line("<AbaConnectContainer>")
        # control counter (TaskCount is actually the number of transactions)
        transaction_count = 0
        transaction_count_identifier = "<!-- $COUNT -->"
        content += make_line(" <TaskCount>{0}</TaskCount>".format(transaction_count_identifier))
        # task container
        content += make_line(" <Task>")
        # parameters
        content += make_line("  <Parameter>")
        content += make_line("   <Application>FIBU</Application>")
        content += make_line("   <Id>XML Buchungen</Id>")
        content += make_line("   <MapId>AbaDefault</MapId>")
        content += make_line("   <Version>2015.00</Version>")
        content += make_line("  </Parameter>")

        # add payment entry transactions
        sql_query = """SELECT 
                      `tabAccount`.`account_number`, 
                      SUM(`tabGL Entry`.`debit`) AS `debit`, 
                      SUM(`tabGL Entry`.`credit`) AS `credit`,
                      `tabGL Entry`.`account_currency` AS `currency`                      
                    FROM `tabGL Entry`
                    LEFT JOIN `tabAccount` ON `tabGL Entry`.`account` = `tabAccount`.`name`
                    WHERE `tabGL Entry`.`posting_date` >= '{start_date}' 
                      AND `tabGL Entry`.`posting_date` <= '{end_date}'
                      AND `tabGL Entry`.`docstatus` = 1
                      AND `tabGL Entry`.`exported_to_abacus` = 0
                    GROUP BY `tabAccount`.`account_number`;
            """.format(start_date=start_date, end_date=end_date)
        items = frappe.db.sql(sql_query, as_dict=True)
        # mark all entries as exported
        export_matches = frappe.get_all("GL Entry", filters=[
            ["posting_date",">=", start_date],
            ["posting_date","<=", end_date],
            ["docstatus","=", 1],
		    ["exported_to_abacus","=",0]], fields=['name'])
        for export_match in export_matches:
            record = frappe.get_doc("GL Entry", export_match['name'])
            record.exported_to_abacus = 1
            record.save(ignore_permissions=True)
        for item in items:
            if item.account_number:
                if item.credit != 0:
                    transaction_count += 1        
                    content += add_transaction_block(item.account_number, item.credit, 
                        "C", end_date, item.currency, transaction_count)
                if item.debit != 0:
                    transaction_count += 1        
                    content += add_transaction_block(item.account_number, item.debit, 
                        "D", end_date, item.currency, transaction_count)
        # add footer
        content += make_line(" </Task>")
        content += make_line("</AbaConnectContainer>")
        # insert control numbers
        content = content.replace(transaction_count_identifier, "{0}".format(transaction_count))
        
        return { 'content': content }
    #except IndexError:
    #    frappe.msgprint( _("Please select at least one payment."), _("Information") )
    #    return
    #except:
    #    frappe.throw( _("Error while generating xml. Make sure that you made required customisations to the DocTypes.") )
    #    return
    
    def get_view_total(self, view_name):
        """ executes a tax lookup query for a total 
        
        """
        sql_query = ("""SELECT IFNULL(SUM(`base_net_total`), 0) AS `total` 
                FROM `{0}` 
                WHERE `posting_date` >= '{1}' 
                AND `posting_date` <= '{2}'""".format(view_name, self.start_date, self.end_date))
        total = frappe.db.sql(sql_query, as_dict=True)
        return { 'total': total[0].total }

    def get_view_tax(self, view_name):
        """ executes a tax lookup query for a tax 
        
        """
        sql_query = ("""SELECT IFNULL(SUM(`total_taxes_and_charges`), 0) AS `total` 
                FROM `{0}` 
                WHERE `posting_date` >= '{1}' 
                AND `posting_date` <= '{2}'""".format(view_name, self.start_date, self.end_date))
        total = frappe.db.sql(sql_query, as_dict=True)
        return { 'total': total[0].total }
      
    def get_tax_rate(self, taxes_and_charges_template):
        sql_query = ("""SELECT `rate` 
            FROM `tabPurchase Taxes and Charges` 
            WHERE `parent` = '{0}' 
            ORDER BY `idx`;""".format(taxes_and_charges_template))
        result = frappe.db.sql(sql_query, as_dict=True)
        if result:
            return result[0].rate
        else:
            return 0
