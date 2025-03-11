import frappe
from erpnext.accounts.party import get_party_account


class SalesDiscountJvAuditor:
    def __init__(self, name) -> None:
        self.invoice_doc = frappe.get_doc("Sales Invoice", name)
        self.jv_dict = None
        self.jv_doc_name = "Journal Entry"

    def add_debit_note(self) -> None:
        debit_note: dict = {"account": get_party_account("Customer", self.invoice_doc.customer, self.invoice_doc.company),
                            "party_type": "Customer",
                            "party": self.invoice_doc.customer,
                            "debit_in_account_currency": self.invoice_doc.custom_grand_total_discount,
                            "reference_type": "Sales Invoice",
                            "reference_name": self.invoice_doc.name,
                            "cost_center": self.invoice_doc.cost_center}
        self.jv_dict["accounts"].append(debit_note)

    def add_credit_note(self) -> None:
        company = frappe.get_doc("Company", self.invoice_doc.company)
        account = company.default_discount_account if company.default_discount_account else f"Sales - {company.abbr}"
        for item in self.invoice_doc.items:
            credit_note: dict = {
                "account":account,
                "credit_in_account_currency": item.custom_total_discount,
                "cost_center": item.cost_center}
            self.jv_dict["accounts"].append(credit_note)

    def add_accounting_entries(self) -> None:
        self.add_debit_note()
        self.add_credit_note()

    def form_jv_dict(self) -> None:
        self.jv_dict = {"doctype": self.jv_doc_name,
                         "naming_series": "D.{bill_no}.-.#",
                         "voucher_type": self.jv_doc_name,
                         "company": self.invoice_doc.company,
                         "posting_date": self.invoice_doc.posting_date,
                         "accounts": [],
                         "bill_no": self.invoice_doc.name,
                         "letter_head": self.invoice_doc.letter_head,
                         "is_opening": "No"
                         }
        self.add_accounting_entries()

    def validate(self) -> bool:
        if self.invoice_doc.custom_submit_discount_entry == 0:
            return False
        return True

    def create_jv(self) -> None:
        if not self.validate():
            return
        self.form_jv_dict()
        jv_doc = frappe.get_doc(self.jv_dict)
        jv_doc.insert()
        jv_doc.submit()

    def cancel_jv(self):
        jvs = frappe.get_all(self.jv_doc_name, filters={"bill_no": self.invoice_doc.name})
        for jv in jvs:
            jv_doc = frappe.get_doc(self.jv_doc_name, jv['name'])
            jv_doc.cancel()


@frappe.whitelist()
def create_discount_jv(invoice_name: str):
    SalesDiscountJvAuditor(invoice_name).create_jv()


@frappe.whitelist()
def cancel_discount_jv(invoice_name: str):
    SalesDiscountJvAuditor(invoice_name).cancel_jv()
