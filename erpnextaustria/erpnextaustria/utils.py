# -*- coding: utf-8 -*-
# Copyright (c) 2018, Fink Zeitsysteme/libracore and contributors
# For license information, please see license.txt

# imports
import frappe
from zeep import Client

# UID validation
#
# Returns a dict with the attribute 'valid' = "True" or "False"
@frappe.whitelist()
def check_uid(uid):
    client = Client('http://ec.europa.eu/taxation_customs/vies/checkVatService.wsdl')
    result = client.service.checkVat(uid[0:2], uid[2:])
    return result.valid

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
        content += make_line("  <InvoiceNumber>{0}</InvoiceNumber>".format(sales_invoice.name))
        content += make_line("  <InvoiceDate>{0}</InvoiceDate>".format(sales_invoice.posting_date))  # yyyy-mm-dd
		# Details zur Lieferung 
		content += make_line("  <Delivery>")
        content += make_line("    <Date>2018-01-01</Date>")
        content += make_line("    <Address>")
        content += make_line("      <Name>Mustermann GmbH</Name>")
        content += make_line("      <Street>Hauptstraße 10</Street>")
        content += make_line("      <Town>Graz</Town>")
        content += make_line("      <ZIP>8010</ZIP>")
        content += make_line("      <Country CountryCode=\"AT\">Österreich</Country>")
        content += make_line("    </Address>")
        content += make_line("    <Contact>")
        content += make_line("      <Salutation>Firma</Salutation>")
        content += make_line("      <Name>Hr. Max Mustermann</Name>")
        content += make_line("    </Contact>")
        content += make_line("  </Delivery>")
		# Rechnungssteller 
		content += make_line("  <Biller>")
        content += make_line("    <VATIdentificationNumber>ATU13585627</VATIdentificationNumber>")
        content += make_line("    <Address>")
        content += make_line("      <Name>Mustermann GmbH</Name>")
        content += make_line("      <Street>Hauptstraße 10</Street>")
        content += make_line("      <Town>Graz</Town>")
        content += make_line("      <ZIP>8010</ZIP>")
        content += make_line("      <Country CountryCode=\"AT\">Österreich</Country>")
		# An die folgende E-Mail-Adresse werden die E-Mails gesendet: 
        content += make_line("      <Email>kontakt@example.org</Email>")
        content += make_line("    </Address>")
        content += make_line("    <Contact>")
        content += make_line("      <Salutation>Firma</Salutation>")
        content += make_line("      <Name>Hr. Max Mustermann</Name>")
        content += make_line("    </Contact>")
		# Die Lieferantennummer/Kreditorennummer: 
        content += make_line("    <InvoiceRecipientsBillerID>0011025781</InvoiceRecipientsBillerID>")
        content += make_line("  </Biller>")
		# Rechnungsempfänger 
		content += make_line("  <InvoiceRecipient>")
		content += make_line("    <VATIdentificationNumber>ATU13585627</VATIdentificationNumber>")
		#content += make_line("    <FurtherIdentification IdentificationType=\"FS\">Wien</FurtherIdentification>")
		#content += make_line("    <FurtherIdentification IdentificationType=\"FN\">12345678</FurtherIdentification>")
		#content += make_line("    <FurtherIdentification IdentificationType=\"FBG\">Handelsgericht Wien</FurtherIdentification>")
		# Die Auftragsreferenz:
		content += make_line("    <OrderReference>")
        content += make_line("      <OrderID>Z01</OrderID>")
        content += make_line("      <ReferenceDate>2012-11-18</ReferenceDate>")
        content += make_line("      <Description>Bestellung neuer Bedarfsmittel</Description>")
        content += make_line("    </OrderReference>")
        content += make_line("    <Address>")
        content += make_line("      <Name>BRZ GmbH</Name>")
        content += make_line("      <Street>Hintere Zollamtsstraße 4</Street>")
        content += make_line("      <Town>Wien</Town>")
        content += make_line("      <ZIP>1030</ZIP>")
        content += make_line("      <Country CountryCode=\"AT\">Österreich</Country>")
        content += make_line("      <Phone>+43 / 1 / 78 56 789</Phone>")
        content += make_line("      <Email>support-erb@brz.gv.at; info@brz.gv.at</Email>")
        content += make_line("    </Address>")
        content += make_line("    <Contact>")
        content += make_line("      <Salutation>Frau</Salutation>")
        content += make_line("      <Name>Maxime Musterfrau</Name>")
        content += make_line("    </Contact>")
        content += make_line("  </InvoiceRecipient>")
        content += make_line("  <Details>")
        #content += make_line("    <HeaderDescription>Optionaler Kopftext für alle Details</HeaderDescription>")
        content += make_line("    <ItemList>")
        content += make_line("      <HeaderDescription>Optionaler Kopftext für diese ItemList</HeaderDescription>")
        content += make_line("      <ListLineItem>")
        content += make_line("        <Description>Schraubenzieher</Description>")
        content += make_line("        <Quantity Unit=\"STK\">100</Quantity>")
        content += make_line("        <UnitPrice>10.20</UnitPrice>")
        content += make_line("        <InvoiceRecipientsOrderReference>")
        content += make_line("          <OrderID>Z01</OrderID>")
        content += make_line("          <OrderPositionNumber>1</OrderPositionNumber>")
        content += make_line("        </InvoiceRecipientsOrderReference>")
        content += make_line("        <TaxItem>")
        content += make_line("          <TaxableAmount>1020</TaxableAmount>")
        content += make_line("          <TaxPercent TaxCategoryCode=\"S\">20</TaxPercent>")
        content += make_line("        </TaxItem>")
        content += make_line("        <LineItemAmount>1020.00</LineItemAmount>     ")   
        content += make_line("      </ListLineItem>")
        #content += make_line("      <FooterDescription>Optionaler Fusstext für diese ItemList</FooterDescription>")
        content += make_line("    </ItemList>")
        #content += make_line("    <FooterDescription>Optionaler Fusstext für alle Details</FooterDescription>")
        content += make_line("  </Details>")
        content += make_line("  <Tax>")
        content += make_line("    <TaxItem>")
        content += make_line("      <TaxableAmount>1130.00</TaxableAmount>")
        content += make_line("      <TaxPercent TaxCategoryCode=\"S\">20.00</TaxPercent>")
        content += make_line("      <TaxAmount>226.00</TaxAmount>")
        content += make_line("    </TaxItem>")
        content += make_line("  </Tax>")
        content += make_line("  <TotalGrossAmount>1361.50</TotalGrossAmount>")
        content += make_line("  <PayableAmount>1361.50</PayableAmount>")
        content += make_line("  <PaymentMethod>")
        content += make_line("    <Comment>Wir ersuchen um termingerechte Bezahlung.</Comment>")
        content += make_line("    <UniversalBankTransaction>")
        content += make_line("      <BeneficiaryAccount>")
        content += make_line("        <BIC>BKAUATWW</BIC>")
        content += make_line("        <IBAN>AT611904300234573201</IBAN>")
        content += make_line("        <BankAccountOwner>Max Mustermann</BankAccountOwner>")
        content += make_line("      </BeneficiaryAccount>")
        content += make_line("    </UniversalBankTransaction>")
        content += make_line("  </PaymentMethod>")
        content += make_line("  <PaymentConditions>")
        content += make_line("    <DueDate>{0}</DueDate>".format(sales_invoice.due_date)
        #content += make_line("    <Discount>")
        #content += make_line("      <PaymentDate>2018-12-10</PaymentDate>")
        #content += make_line("      <Percentage>3.00</Percentage>")
        #content += make_line("    </Discount>")
        #content += make_line("    <Comment>Kommentar zu den Zahlungsbedingungen</Comment>")
        content += make_line("  </PaymentConditions>")
        #content += make_line("  <Comment>Globaler Kommentar zur Rechnung.</Comment>")
        content += make_line("</Invoice>")
        return { 'content': content }
    except:
        frappe.throw( _("Error while generating xml. Make sure that you made required customisations to the DocTypes.") )
        return

# adds Windows-compatible line endings (to make the xml look nice)    
def make_line(line):
    return line + "\r\n"