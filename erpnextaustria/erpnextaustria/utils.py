# -*- coding: utf-8 -*-
# Copyright (c) 2018-2023, Fink Zeitsysteme/libracore and contributors
# For license information, please see license.txt
#
# Import exchange rates
#  $ bench execute erpnextaustria.erpnextaustria.utils.read_exchange_rates --kwargs "{'currencies': ['CHF']}"
#

# imports
import frappe
from frappe import _
from zeep import Client
import requests
from bs4 import BeautifulSoup
from time import strftime

# UID validation
#
# Returns a dict with the attribute 'valid' = "True" or "False"
@frappe.whitelist()
def check_uid(uid):
    try:
        result = vat_request(uid)
    except:
        try:
            # second try
            result = vat_request(uid)
        except Exception as e:
            frappe.throw( _("Unable to validate UID. Please try again in a few seconds.") )
    return result.valid

def vat_request(uid):
    client = Client('http://ec.europa.eu/taxation_customs/vies/checkVatService.wsdl')
    result = client.service.checkVat(uid[0:2], uid[2:])
    return result

# Creation of ebInterface invoice file (following ebInterface 5.0)
#
# Returns an XML-File for a Sales Invoice
@frappe.whitelist()
def create_ebinterface_xml(sinv, with_details=1):
    if True: #try:
        # collect information
        sales_invoice = frappe.get_doc("Sales Invoice", sinv)
        try:
            company_address = frappe.get_doc("Address", sales_invoice.company_address)
            company_country = frappe.get_doc("Country", company_address.country)
        except Exception as err:
            frappe.throw( _("Company address {0} not found ({1}). Please set an address for company {2}.").format(sales_invoice.company_address, err.message, sinv.company))
        # Details zur Lieferung
        if sales_invoice.items[0].delivery_note:
            try:
                delivery_note = frappe.get_doc("Delivery Note", sales_invoice.items[0].delivery_note)
                delivery_date = delivery_note.posting_date
            except:
                frappe.msgprint(_("Unable to find delivery note"))
        else:
            delivery_date = sales_invoice.posting_date
        owner = frappe.get_doc("User", sales_invoice.owner)
        # Die Lieferantennummer/Kreditorennummer: 
        customer = frappe.get_doc("Customer", sales_invoice.customer)
        if not customer.lieferantennummer:
            frappe.throw( _("Customer does not have a supplier number. Please add your supplier number to the customer record.") )
        if not customer.auftragsreferenz:
            frappe.throw( _("Customer does not have an order reference. Please add your order reference to the customer record.") )
        try:
            customer_address = frappe.get_doc("Address", sales_invoice.customer_address)
            customer_country = frappe.get_doc("Country", customer_address.country)
        except Exception as err:
            frappe.throw( _("Customer address {0} not found ({1}).").format(sales_invoice.customer_address, err.message))
        if sales_invoice.items[0].sales_order:
            try:
                so = frappe.get_doc("Sales Order", sales_invoice.items[0].sales_order)
                sales_order = {
                    'posting_date': so.transaction_date,
                    'description': so.po_no or ""
                }
            except:
                frappe.msgprint(_("Unable to find sales order"))
        else:
            sales_order = None
        contact = frappe.get_doc("Contact", sales_invoice.contact_person)
        # bank account
        company = frappe.get_doc("Company", sales_invoice.company)
        bank_account = frappe.get_doc("Account", company.default_bank_account)

        # create xml header
        data = {
            'sales_invoice': {
                'name': sales_invoice.name,
                'posting_date': sales_invoice.posting_date,
                'company': sales_invoice.company,
                'owner': sales_invoice.owner,
                'customer_name': sales_invoice.customer_name,
                'net_total': sales_invoice.net_total,
                'grand_total': sales_invoice.grand_total,
                'due_date': sales_invoice.due_date
            },
            'delivery': {
                'delivery_date': delivery_date
            },
            'company': {
                'address_line1': company_address.address_line1,
                'city': company_address.city,
                'pincode': company_address.pincode,
                'country_code': company_country.code,
                'country_name': company_country.name,
                'tax_id': company.tax_id,
                'firmensitz': company.firmensitz,
                'firmenbuchnummer': company.firmenbuchnummer,
                'firmenbuchgericht': company.firmenbuchgericht,
                'name': company.name
            },
            'owner': {
                'full_name': owner.full_name
            },
            'customer': {
                'lieferantennummer': customer.lieferantennummer,
                'tax_id': customer.tax_id,
                'auftragsreferenz': customer.auftragsreferenz,
                'address_line1': customer_address.address_line1,
                'city': customer_address.city,
                'pincode': customer_address.pincode,
                'country_code': customer_country.code,
                'country_name': customer_country.name
            },
            'sales_order': sales_order,
            'contact': {
                'salutation': contact.salutation,
                'first_name': contact.first_name,
                'last_name': contact.last_name,
                'phone': contact.phone,
                'email_id': contact.email_id
            },
            'items': [],
            'taxes': [],
            'bank_account': {
                'bic': bank_account.bic,
                'iban': bank_account.iban
            },
            'with_details': with_details
        }
        # add items
        for index, item in enumerate(sales_invoice.items, start=1):
            i = {
                'item_name': item.item_name,
                'uom': item.uom, 
                'qty': item.qty,
                'rate': item.rate,
                'index': index,
                'amount': item.amount,
                'tax_percent': 20
            }
            data['items'].append(i)
        # add taxes
        for tax in sales_invoice.taxes:
            t = {
                'rate': tax.rate,
                'tax_amount': tax.tax_amount
            }
            data['taxes'].append(t)
        # render xml
        content = frappe.render_template('erpnextaustria/templates/ebi5p0.html', data)
        return { 'content': content }
    #except Exception as err:
    #    frappe.throw( _("Error while generating xml. Make sure that you made required customisations to the DocTypes. {0}").format(err.message) )
    #    return

# adds Windows-compatible line endings (to make the xml look nice)    
def make_line(line):
    return line + "\r\n"

@frappe.whitelist()
def get_eur_exchange_rate(currency):
    url = "https://www.oenb.at/isaweb/reportExcelHtml.do?report=2.14.9&sort=ASC&dynValue=0&lang=DE&linesPerPage=allen&timeSeries=All&page=1"
    page = requests.get(url)
    if page.status_code == 200:
        # all good, parse
        soup = BeautifulSoup(page.text, 'lxml')
        # find all currency nodes
        currency_rows = soup.find_all('tr')
        # evaluate each node
        for cr in currency_rows:
            # parse fields
            fields = cr.find_all('td')
            # only use rows with 11 cells
            if len(fields) == 11:
                # parse currency code and exchange rate
                try:
                    currency_code = fields[1].get_text().replace('\n', '').replace('\r', '').replace('\t', '')
                    raw = fields[-1].get_text().replace('\n', '').replace('\r', '').replace('\t', '').replace('.', '').replace(',', '.')
                    exchange_rate = float(raw)
                    # return if matched
                    print("{0}: 1 EUR = {1} {0}".format(currency_code, exchange_rate))
                    if currency.lower() == currency_code.lower():
                        return exchange_rate
                except:
                    print("parsing error {0}".format(raw))
                    # skip errors, probably an illegal row (like header)
                    pass
    else:
        # failed
        frappe.log_error("Unable to get exchange rate (error code {0})".format(page.status_code), 
            "Get exchange rate failed")
    return

def read_exchange_rates(currencies=["CHF"]):
    for c in currencies:
        rate = get_eur_exchange_rate(c)
        create_exchange_rate(c, rate)
        create_exchange_rate("EUR", (1/rate), c)    # create inverse conversion rate
    return
    
def create_exchange_rate(to_currency, rate, from_currency="EUR"):
    # insert a new record in ERPNext
    # Exchange Rate (1 EUR = [?] to_currency)
    date = strftime("%Y-%m-%d")
    new_exchange_rate = frappe.get_doc({
        'doctype': "Currency Exchange",
        'date': date,
        'from_currency': from_currency,
        'to_currency': to_currency,
        'exchange_rate': rate
    })
    try:
        record = new_exchange_rate.insert()  
    except frappe.exceptions.DuplicateEntryError:
        print("There is already an exchange rate for {0} on {1}".format(from_currency, date))
        record = None
    except Exception as err:
        print(err.message)
        record = None
    return record
