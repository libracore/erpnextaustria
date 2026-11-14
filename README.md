# ERPNextAustria
Country-specific extensions for ERPNext in Austria

ERPNext ([https://www.erpnext.org](https://www.erpnext.org)) is a global, leading, cloud based
open source enterprise resource planning software. ERPNext is a trademark by Frappé Technologies.

The ERPNextAustria application adds country-specific features to this platform such as 
bank, tax and payment integrations.

## License 
GNU Affero General Public License, refer to LICENSE

ERPNextAustria is developed and maintained by libracore and contributors. 
The copyright is owned by libracore and contributors. 
The software comes as-is without any warranty.

## Requirements
Requires an ERPNext server instance (refer to [https://github.com/frappe/erpnext](https://github.com/frappe/erpnext))

## Installation
From the frappe-bench folder, execute

    $ bench get-app https://github.com/libracore/erpnextaustria.git
    $ bench install-app erpnextaustria

## Features 
* Tax
    * VAT declaration

## Release notes
Refer to [https://github.com/libracore/erpnextaustria/wiki/Release-Notes](https://github.com/libracore/erpnextaustria/wiki/Release-Notes)

## Important notes
* The UVA PDF generation only works, if `pdftk` is installed. For more information see https://wiki.ubuntuusers.de/pdftk/#Installation.

    ```
    $ sudo apt install pdftk
    ```

    Or, for Ubuntu 18.04:

    ```
    $ sudo snap install pdftk
    ```

## U30 XML export

The XML export uses the BMF schema effective for the declaration period:
01/2022 through June/Q2 2026, and 07/2026 from July/Q3 2026 onwards.
The selected official XSD URL is included in `xsi:noNamespaceSchemaLocation`;
exporting does not download the schema or submit data. Periods must be complete
calendar months or quarters from 2022 onwards. Optional amounts which serialize
to zero are omitted; KZ000 is always included.

Existing declaration amount fields are exported in BMF order, including KZ016
(`small_businesses`). KZ057 (`tax_057`) is exported under `VERSTEUERT`; KZ066
(`taxation_pretax`) is independent and must only contain eligible input tax.
KZ095 is a calculated total and is not an XML element.

For installations with data for the new KZ124/KZ125, the exporter also accepts
optional Currency custom fields `amount_124` and `amount_125` on `AT VAT Declaration`.
These are the corresponding taxable bases (not calculated tax amounts). Missing
fields are treated as zero. Nonzero values before July/Q3 2026 are rejected.
The export does not create these fields, fetch their values or change the form's
existing tax calculations, PDF or journal logic. Review those separately if using
the new bases in the form. The current 07/2026 schema is also used for later
periods until a replacement is implemented.

See [U30 regression tests and official sources](tests/README.md) for validation.
