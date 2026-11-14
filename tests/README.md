# U30 XML regression tests

Run from the repository root with Python 3.8+:

```sh
python3 -m pip install -r tests/requirements.txt
timeout 120 python3 -m unittest discover -s tests -v
```

The tests exercise the production export data builder and Jinja template without
an ERPNext database. A controller smoke test stubs the Frappe/PDF dependencies;
a full bench/UI integration test is still needed before deployment. All tax
numbers, names and amounts in these tests are synthetic. No FinanzOnline login,
submission or production tax data is used.

The two original XSDs are downloaded directly from the Austrian Federal Ministry
of Finance (BMF), with a 20-second timeout and a 256 KiB read limit per download.
A source change or failed download fails the suite rather than skipping validation.
For offline runs set `U30_XSD_DIR` to a directory containing both files under their
original filenames. The hashes below are checked in either mode.

| Effective period | Source | SHA-256 (original bytes) |
| --- | --- | --- |
| January 2022 through June/Q2 2026 | [BMF XSD 01/2022](https://www.bmf.gv.at/dam/jcr:5deafd50-12d6-4ac3-a9f7-0e234c690db2/BMF_ERKLAERUNGS_UEBERMITTLUNG_U30_01_2022.xsd) | `484bdff6e41ab80a18abe7331cc2720494dbf09d0438eaedd0a8db6be5124551` |
| July/Q3 2026 onwards | [BMF XSD 07/2026](https://www.bmf.gv.at/dam/jcr:2e90eb5d-ef76-48a8-922b-dbf62cc2f230/BMF_ERKLAERUNGS_UEBERMITTLUNG_U30_07_2026.xsd) | `e51a69c99568f2d9fbccf9271d6243d9880588561a30746303ad6c23d646f757` |

Sources checked on 2026-11-14. The XSD header dates are 2021-09-28 and 2026-04-24.
The BMF publishes these documents for software manufacturers on its
[official download page](https://www.bmf.gv.at/services/finanzonline/informationen-fuer-softwarehersteller/softwarehersteller-erklarungen-und-antraege.html).
They are third-party official material, not files covered by this repository's
AGPL notice. No explicit redistribution license is asserted here; the test suite
downloads the original documents instead of vendoring or relicensing them.
See also the [BMF change notice](https://www.bmf.gv.at/dam/jcr:922a2cf9-e758-40c4-a671-1674044cced1/BMF_Dokumentenversion_UVA%20ab_07_2026.pdf)
and [additional business checks](https://www.bmf.gv.at/dam/jcr:4180aed7-d33e-4949-b0ca-5999aaa185c6/BMF_Pruefungen_UVA_ab_07_2026.pdf).

Coverage includes small businesses (only KZ000/KZ016), reverse charge without
input-tax entitlement (KZ057 and zero KZ000, no KZ066), standard taxation with
intra-community acquisitions, Q3 2026 with KZ124/KZ125, monthly/quarterly boundaries,
date objects, missing/zero/rounded-zero amounts, escaped company names and invalid
periods. Mutation checks prove that the XSDs reject the original zero/order errors
and a misplaced KZ057. XSD validity does not replace the BMF business checks.

All populated KZ amounts are compared against explicit expected dictionaries,
including every existing supported field under both current schemas. Removing
KZ012 from the mapping now fails the field comparisons for both schema versions.
Nonzero KZ020 (`tax_free_revenue`, after rounding) is rejected with a VST explanation
before XML rendering: the required exemption-reason field is not supported by
this DocType. Missing and rounded-zero KZ020 values remain omitted.

Periods wholly before January 2022 retain the original export structure, field
set, numeric formatting and optional zero elements, without a newer schema URL
or the newer calendar-period restrictions. These historical exports are compared
to `fixtures/u30_legacy.xml`, frozen from upstream commit `68d66a1` with synthetic
values and a fixed timestamp. They are deliberately not validated against the
2022/2026 XSDs. XML escaping also applies to historical company names/identifiers.
Nonzero KZ124/KZ125 remain rejected before July 2026, including historical periods.
