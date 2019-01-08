# -*- coding: utf-8 -*-
# Copyright (c) 2018, Fink Zeitsysteme/libracore and contributors
# For license information, please see license.txt

# imports
import frappe
from frappe import _
from zeep import Client

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
def create_ebinterface_xml(sinv):
    try:
        sales_invoice = frappe.get_doc("Sales Invoice", sinv)

        # create xml header
        content = make_line("<?xml version=\"1.0\" encoding=\"UTF-8\"?>")
        content += make_line("""<Invoice xmlns=\"http://www.ebinterface.at/schema/5p0/\"
            GeneratingSystem=\"ERPNext\"
            DocumentType=\"Invoice\"
            InvoiceCurrency=\"EUR\"
            Language=\"ger\">""")
        content += make_line(u"  <InvoiceNumber>{0}</InvoiceNumber>".format(sales_invoice.name))
        content += make_line(u"  <InvoiceDate>{0}</InvoiceDate>".format(sales_invoice.posting_date))  # yyyy-mm-dd
        # Details zur Lieferung
        try:
            company_address = frappe.get_doc("Address", sales_invoice.company_address)
            company_country = frappe.get_doc("Country", company_address.country)
        except Exception as err:
            frappe.throw( _("Company address {0} not found ({1}). Please set an address for company {2}.").format(sales_invoice.company_address, err.message, sinv.company))
        if sales_invoice.items[0].delivery_note:
            try:
                delivery_note = frappe.get_doc("Delivery Note", sales_invoice.items[0].delivery_note)
            except:
                frappe.msgprint(_("Unable to find delivery note"))
        content += make_line("  <Delivery>")
        try:
            content += make_line("    <Date>{0}</Date>".format(delivery_note.posting_date))
        except:
            content += make_line("    <Date>{0}</Date>".format(sales_invoice.posting_date))
        content += make_line("    <Address>")
        content += make_line(u"      <Name>{0}</Name>".format(sales_invoice.company))
        content += make_line(u"      <Street>{0}</Street>".format(company_address.address_line1))
        content += make_line(u"      <Town>{0}</Town>".format(company_address.city))
        content += make_line(u"      <ZIP>{0}</ZIP>".format(company_address.pincode))
        content += make_line(u"      <Country CountryCode=\"{0}\">{1}</Country>".format(company_country.code, company_country.name))
        content += make_line("    </Address>")
        content += make_line("    <Contact>")
        owner = frappe.get_doc("User", sales_invoice.owner)
        content += make_line("      <Salutation>Firma</Salutation>")
        content += make_line(u"      <Name>{0}</Name>".format(owner.full_name))
        content += make_line("    </Contact>")
        content += make_line("  </Delivery>")
        # Rechnungssteller
        content += make_line("  <Biller>")
        company = frappe.get_doc("Company", sales_invoice.company)
        content += make_line("    <VATIdentificationNumber>{0}</VATIdentificationNumber>".format(company.tax_id))
        # Zusätzliche Lieferanteninformationen
        content += make_line(u"    <FurtherIdentification IdentificationType=\"FS\">{0}</FurtherIdentification>".format(company.firmensitz))
        content += make_line(u"    <FurtherIdentification IdentificationType=\"FN\">{0}</FurtherIdentification>".format(company.firmenbuchnummer))
        content += make_line(u"    <FurtherIdentification IdentificationType=\"FBG\">{0}</FurtherIdentification>".format(company.firmenbuchgericht))
        content += make_line("    <Address>")
        content += make_line(u"      <Name>{0}</Name>".format(sales_invoice.company))
        content += make_line(u"      <Street>{0}</Street>".format(company_address.address_line1))
        content += make_line(u"      <Town>{0}</Town>".format(company_address.city))
        content += make_line(u"      <ZIP>{0}</ZIP>".format(company_address.pincode))
        content += make_line(u"      <Country CountryCode=\"{0}\">{1}</Country>".format(company_country.code, company_country.name))
        # An die folgende E-Mail-Adresse werden die E-Mails gesendet: 
        content += make_line(u"      <Email>{0}</Email>".format(sales_invoice.owner))
        content += make_line("    </Address>")
        content += make_line("    <Contact>")
        content += make_line("      <Salutation>Firma</Salutation>")
        content += make_line(u"      <Name>{0}</Name>".format(owner.full_name))
        content += make_line("    </Contact>")
        # Die Lieferantennummer/Kreditorennummer: 
        customer = frappe.get_doc("Customer", sales_invoice.customer)
        if not customer.lieferantennummer:
            frappe.throw( _("Customer does not have a supplier number. Please add your supplier number to the customer record.") )
        content += make_line(u"    <InvoiceRecipientsBillerID>{0}</InvoiceRecipientsBillerID>".format(customer.lieferantennummer))
        content += make_line("  </Biller>")
        # Rechnungsempfänger 
        content += make_line("  <InvoiceRecipient>")
        content += make_line(u"    <VATIdentificationNumber>{0}</VATIdentificationNumber>".format(customer.tax_id))
        # Die Auftragsreferenz:
        content += make_line("    <OrderReference>")
        if not customer.auftragsreferenz:
            frappe.throw( _("Customer does not have an order reference. Please add your order reference to the customer record.") )
        content += make_line(u"      <OrderID>{0}</OrderID>".format(customer.auftragsreferenz))
        if sales_invoice.items[0].sales_order:
            try:
                sales_order = frappe.get_doc("Sales Order", sales_invoice.items[0].sales_order)
                content += make_line(u"      <ReferenceDate>{0}</ReferenceDate>".format(sales_order.posting_date))
                content += make_line(u"      <Description>{0}</Description>".format(sales_order.po_no or ""))
            except:
                frappe.msgprint(_("Unable to find sales order"))
        content += make_line("    </OrderReference>")
        try:
            customer_address = frappe.get_doc("Address", sales_invoice.customer_address)
            customer_country = frappe.get_doc("Country", customer_address.country)
        except Exception as err:
            frappe.throw( _("Customer address {0} not found ({1}).").format(sales_invoice.customer_address, err.message))
        content += make_line("    <Address>")
        content += make_line(u"      <Name>{0}</Name>".format(sales_invoice.customer_name))
        content += make_line(u"      <Street>{0}</Street>".format(customer_address.address_line1))
        content += make_line(u"      <Town>{0}</Town>".format(customer_address.city))
        content += make_line(u"      <ZIP>{0}</ZIP>".format(customer_address.pincode))
        content += make_line(u"      <Country CountryCode=\"{0}\">{1}</Country>".format(customer_country.code, customer_country.name))
        contact = frappe.get_doc("Contact", sales_invoice.contact_person)
        content += make_line(u"      <Phone>{0}</Phone>".format(contact.phone))
        content += make_line(u"      <Email>{0}</Email>".format(contact.email_id))
        content += make_line("    </Address>")
        content += make_line("    <Contact>")
        content += make_line(u"      <Salutation>{0}</Salutation>".format(contact.salutation))
        content += make_line(u"      <Name>{0} {1}</Name>".format(contact.first_name, contact.last_name))
        content += make_line("    </Contact>")
        content += make_line("  </InvoiceRecipient>")
        content += make_line("  <Details>")
        #content += make_line("    <HeaderDescription>Optionaler Kopftext für alle Details</HeaderDescription>")
        content += make_line("    <ItemList>")
        #content += make_line("      <HeaderDescription>Optionaler Kopftext für diese ItemList</HeaderDescription>")
        for item in sales_invoice.items:
            content += make_line("      <ListLineItem>")
            content += make_line(u"        <Description>{0}</Description>".format(item.item_name))
            content += make_line(u"        <Quantity Unit=\"{0}\">{1}</Quantity>".format(item.uom, item.qty))
            content += make_line(u"        <UnitPrice>{0}</UnitPrice>".format(item.rate))
            content += make_line("        <InvoiceRecipientsOrderReference>")
            content += make_line(u"         <OrderID>{0}</OrderID>".format(customer.auftragsreferenz))
            content += make_line("          <OrderPositionNumber>{0}</OrderPositionNumber>".format(loop.index))
            content += make_line("        </InvoiceRecipientsOrderReference>")
            content += make_line("        <TaxItem>")
            content += make_line("          <TaxableAmount>{0}</TaxableAmount>".format(item.amount))
            content += make_line("          <TaxPercent TaxCategoryCode=\"S\">20</TaxPercent>")
            content += make_line("        </TaxItem>")
            content += make_line("        <LineItemAmount>{0}</LineItemAmount>".format(item.amount))   
            content += make_line("      </ListLineItem>")
        #content += make_line("      <FooterDescription>Optionaler Fusstext für diese ItemList</FooterDescription>")
        content += make_line("    </ItemList>")
        #content += make_line("    <FooterDescription>Optionaler Fusstext für alle Details</FooterDescription>")
        content += make_line("  </Details>")
        for tax in sales_invoice.taxes:
            content += make_line("  <Tax>")
            content += make_line("    <TaxItem>")
            content += make_line("      <TaxableAmount>{0}</TaxableAmount>".format(sales_invoice.net_total))
            content += make_line("      <TaxPercent TaxCategoryCode=\"S\">{0}</TaxPercent>".format(tax.rate))
            content += make_line("      <TaxAmount>{0}</TaxAmount>".format(tax.tax_amount))
            content += make_line("    </TaxItem>")
            content += make_line("  </Tax>")
        content += make_line("  <TotalGrossAmount>{0}</TotalGrossAmount>".format(sales_invoice.grand_total))
        content += make_line("  <PayableAmount>{0}</PayableAmount>".format(sales_invoice.grand_total))
        content += make_line("  <PaymentMethod>")
        content += make_line("    <Comment>Wir ersuchen um termingerechte Bezahlung.</Comment>")
        content += make_line("    <UniversalBankTransaction>")
        content += make_line("      <BeneficiaryAccount>")
        bank_account = frappe.get_doc("Account", company.default_bank_account)
        content += make_line("        <BIC>{0}</BIC>".format(bank_account.bic))
        content += make_line("        <IBAN>{0}</IBAN>".format(bank_account.iban))
        content += make_line("        <BankAccountOwner>{0}</BankAccountOwner>".format(company.name))
        content += make_line("      </BeneficiaryAccount>")
        content += make_line("    </UniversalBankTransaction>")
        content += make_line("  </PaymentMethod>")
        content += make_line("  <PaymentConditions>")
        content += make_line("    <DueDate>{0}</DueDate>".format(sales_invoice.due_date))
        #content += make_line("    <Discount>")
        #content += make_line("      <PaymentDate>2018-12-10</PaymentDate>")
        #content += make_line("      <Percentage>3.00</Percentage>")
        #content += make_line("    </Discount>")
        #content += make_line("    <Comment>Kommentar zu den Zahlungsbedingungen</Comment>")
        content += make_line("  </PaymentConditions>")
        #content += make_line("  <Comment>Globaler Kommentar zur Rechnung.</Comment>")
        content += make_line("</Invoice>")
        return { 'content': content }
    except Exception as err:
        frappe.throw( _("Error while generating xml. Make sure that you made required customisations to the DocTypes. {0}").format(err.message) )
        return

# adds Windows-compatible line endings (to make the xml look nice)    
def make_line(line):
    return line + "\r\n"
