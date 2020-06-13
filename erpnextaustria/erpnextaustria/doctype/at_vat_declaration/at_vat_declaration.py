# -*- coding: utf-8 -*-
# Copyright (c) 2018, libracore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from datetime import datetime

class ATVATDeclaration(Document):
    # generate xml export
    def generate_transfer_file(self):
        #try:
        fastnr = frappe.get_value("ERPNextAustria Settings", "ERPNextAustria Settings", "fastnr")
        now = datetime.now()
        data = {
            'fastnr': fastnr,
            'datum': "{0:04d}-{1:02d}-{2:02d}".format(now.year, now.month, now.day),
            'zeit': "{0:02d}:{1:02d}:{2:02d}".format(now.hour, now.minute, now.second),
            'von': "{0}".format(self.start_date[0:7]),
            'bis': "{0}".format(self.end_date[0:7]),
            'kundeninfo': self.company,
            'revenue': self.revenue,
            'exports': self.exports,
            'inner_eu': self.inner_eu,
            'receiver_vat': self.receiver_vat,
            'amount_normal': self.amount_normal,
            'reduced_amount': self.reduced_amount,
            'tax_057': self.tax_057,
            'total_pretax': self.total_pretax,
            'import_pretax': self.import_pretax,
            'import_charge_pretax': self.import_charge_pretax,
            'intercommunla_pretax': self.intercommunal_pretax,
            'taxation_pretax': self.taxation_pretax,
            'intercommunal_revenue': self.intercommunal_revenue,
            'amount_inter_normal': self.amount_inter_normal
        }
        # render template
        content = frappe.render_template('erpnextaustria/erpnextaustria/doctype/at_vat_declaration/u30.html', data)
     
        return { 'content': content }
    #except IndexError:
    #    frappe.msgprint( _("Please select at least one payment."), _("Information") )
    #    return
    #except:
    #    frappe.throw( _("Error while generating xml. Make sure that you made required customisations to the DocTypes.") )
    #    return

# note: do not move below functions into the class, otherwise, saving values will be impossible
@frappe.whitelist()
def get_view_total(view_name, start_date, end_date, company="%"):
    # try to fetch total from VAT query
    if frappe.db.exists("AT VAT query", view_name):
        sql_query = ("""SELECT IFNULL(SUM(`s`.`base_grand_total`), 0) AS `total` 
                FROM ({query}) AS `s` 
                WHERE `s`.`posting_date` >= '{start_date}' 
                AND `s`.`posting_date` <= '{end_date}'""".format(
                query=frappe.get_value("AT VAT query", view_name, "query"),
                start_date=start_date, end_date=end_date).replace("{company}", company))        
    else:
        # fallback database view
        """ executes a tax lookup query for a total 
        
        """
        sql_query = ("""SELECT IFNULL(SUM(`base_grand_total`), 0) AS `total` 
                FROM `{0}` 
                WHERE `posting_date` >= '{1}' 
                AND `posting_date` <= '{2}'""".format(view_name, start_date, end_date))
    total = frappe.db.sql(sql_query, as_dict=True)
    return { 'total': total[0].total }

@frappe.whitelist()
def get_view_tax(view_name, start_date, end_date, company="%"):
    # try to fetch total from VAT query
    if frappe.db.exists("AT VAT query", view_name):
        sql_query = ("""SELECT IFNULL(SUM(`s`.`total_taxes_and_charges`), 0) AS `total` 
                FROM ({query}) AS `s` 
                WHERE `s`.`posting_date` >= '{start_date}' 
                AND `s`.`posting_date` <= '{end_date}'""".format(
                query=frappe.get_value("AT VAT query", view_name, "query"),
                start_date=start_date, end_date=end_date).replace("{company}", company))      
    else:
        # fallback database view
        """ executes a tax lookup query for a tax 
        
        """
        sql_query = ("""SELECT IFNULL(SUM(`total_taxes_and_charges`), 0) AS `total` 
                FROM `{0}` 
                WHERE `posting_date` >= '{1}' 
                AND `posting_date` <= '{2}'""".format(view_name, start_date, end_date))
    total = frappe.db.sql(sql_query, as_dict=True)
    return { 'total': total[0].total }
  
@frappe.whitelist()
def get_tax_rate(taxes_and_charges_template):
    sql_query = ("""SELECT `rate` 
        FROM `tabPurchase Taxes and Charges` 
        WHERE `parent` = '{0}' 
        ORDER BY `idx`;""".format(taxes_and_charges_template))
    result = frappe.db.sql(sql_query, as_dict=True)
    if result:
        return result[0].rate
    else:
        return 0
