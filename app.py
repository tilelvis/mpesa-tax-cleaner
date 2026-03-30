import streamlit as st
import pypdf
import pandas as pd
import re
import io

# --- CONFIGURATION ---
DEFAULT_BANKS = 'im bank, i&m, sidian, kcb, equity, co-op, absa, stanchart, ncba, family, transfer from bank'
DEFAULT_LOANS = 'overdraft, credit, chelete, zenka, tala, branch, m-shwari, fuliza, kcb mpesa, unaitas, advance poa, loan, kcb m-pesa, hustler fund, zash, okash'
DEFAULT_GAMBLING = '1xbet, paystack, betika, sportpesa, odibets, betway, b2c'
DEFAULT_PHONES = '**554, **534'
DEFAULT_NAMES = 'Your mpesa name'

class HustleTaxAnalyzer:
    def __init__(self, my_other_numbers, my_banks, my_names, my_loans, my_gambling, password=None):
        self.personal_ids = [str(n).strip() for n in my_other_numbers if n.strip()]
        self.bank_keywords = [b.lower().strip() for b in my_banks if b.strip()]
        self.personal_names = [n.lower().strip() for n in my_names if n.strip()]
        self.loan_keywords = [l.lower().strip() for l in my_loans if l.strip()]
        self.gambling_keywords = [g.lower().strip() for g in my_gambling if g.strip()]
        self.password = password

    def classify_transaction(self, desc, amt):
        desc = str(desc).lower()

        # Only classify "Money In" (positive amounts)
        if amt <= 0:
            return "Personal Expense"

        # A. Check for Banks
        if any(bank in desc for bank in self.bank_keywords):
            return "ASSET TRANSFER (BANK)"

        # B. Check for Loans/Credit
        if any(loan in desc for loan in self.loan_keywords):
            return "LOAN/CREDIT (NON-TAXABLE)"

        # C. Check for Gambling (Withholding Tax already paid)
        if any(bet in desc for bet in self.gambling_keywords):
            return "EXEMPT (GAMBLING WINNINGS)"

        # D. Check for Self-Transfers (Masked numbers or your Name)
        is_self_id = any(f"******{ide}" in desc or desc.endswith(ide) for ide in self.personal_ids)
        is_self_name = any(name in desc for name in self.personal_names)

        if is_self_id or is_self_name:
            return "ASSET TRANSFER (MOBILE)"

        # E. Remaining is Business Revenue
        return "TAXABLE INCOME"

    def process_pdf(self, pdf_file):
        text = ""
        try:
            reader = pypdf.PdfReader(pdf_file)
            if reader.is_encrypted:
                if self.password:
                    try:
                        reader.decrypt(self.password)
                    except Exception as e:
                        return None, f"Incorrect password or decryption error: {e}"
                else:
                    return None, "This PDF is encrypted. Please provide the password in the sidebar."

            for page in reader.pages:
                text += page.extract_text() + "\n"
        except Exception as e:
            return None, f"Error reading PDF: {e}"

        transactions = []
        current_tx = None
        lines = text.split('\n')
        pattern = r'^([A-Z0-9]{10})\s+(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2})\s+(.*)'

        for line in lines:
            line = line.strip()
            match = re.match(pattern, line)
            if match:
                if current_tx: transactions.append(current_tx)
                current_tx = {'Date': match.group(2), 'Details': match.group(4)}
            elif current_tx:
                current_tx['Details'] += " " + line

        if current_tx: transactions.append(current_tx)
        if not transactions:
            return None, "No transactions found. Ensure this is a standard M-Pesa statement PDF."

        rows = []
        for tx in transactions:
            det = tx['Details']
            m = re.search(r'(Completed|Failed|Cancelled|Pending)\s+([\d,.-]+)\s+([\d,.-]+)$', det)
            if m:
                status = m.group(1).lower()
                amt_str = m.group(2).replace(',', '')
                try:
                    amt = float(amt_str)
                except ValueError:
                    continue

                content = det[:m.start()].strip()
                if status == 'completed':
                    category = self.classify_transaction(content, amt)
                    rows.append({
                        'Date': tx['Date'],
                        'Amount': amt,
                        'Description': content.upper(),
                        'Final_Category': category
                    })

        df = pd.DataFrame(rows, columns=['Date', 'Amount', 'Description', 'Final_Category'])
        return df, None

    def process_csv(self, csv_file):
        try:
            df = pd.read_csv(csv_file)
            # Standard M-Pesa CSV usually has columns like 'Completion Time', 'Details', 'Amount'
            # We normalize to 'Date', 'Amount', 'Description'
            if 'Details' in df.columns and 'Amount' in df.columns:
                df = df.rename(columns={'Details': 'Description', 'Completion Time': 'Date'})
            elif 'Description' not in df.columns or 'Amount' not in df.columns:
                return None, "CSV must contain 'Description' (or 'Details') and 'Amount' columns."

            df['Amount'] = pd.to_numeric(df['Amount'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
            df['Final_Category'] = df.apply(lambda row: self.classify_transaction(row['Description'], row['Amount']), axis=1)
            return df, None
        except Exception as e:
            return None, f"Error reading CSV: {e}"

# --- STREAMLIT UI ---
st.set_page_config(page_title="KRA Hustle-Tax Sanitizer", page_icon="🇰🇪")

st.title("🇰🇪 KRA Hustle-Tax Sanitizer")
st.markdown("""
Upload your M-Pesa **PDF statement** or **CSV report** to filter out bank transfers and loans,
leaving only your **estimated taxable income**.
""")

with st.sidebar:
    st.header("Settings")

    st.info("M-Pesa PDFs are usually encrypted with your ID or Document Number.")
    pdf_password = st.text_input("PDF Password (if encrypted)", type="password")

    st.divider()
    st.info("Define your accounts and names to exclude them from 'Taxable Income'.")

    name_input = st.text_input("Your Registered Names (comma separated)", DEFAULT_NAMES)
    bank_input = st.text_area("Your Bank Names (comma separated)", DEFAULT_BANKS)
    loan_input = st.text_area("Loan Keywords (comma separated)", DEFAULT_LOANS)
    gambling_input = st.text_area("Gambling Keywords (comma separated)", DEFAULT_GAMBLING)
    phone_input = st.text_area("Your Other Phone Numbers / IDs (comma separated)", DEFAULT_PHONES)

    names = [n.strip() for n in name_input.split(",") if n.strip()]
    banks = [b.strip() for b in bank_input.split(",") if b.strip()]
    loans = [l.strip() for l in loan_input.split(",") if l.strip()]
    gambling = [g.strip() for g in gambling_input.split(",") if g.strip()]
    phones = [p.strip() for p in phone_input.split(",") if p.strip()]

uploaded_file = st.file_uploader("Upload M-Pesa Statement (PDF or CSV)", type=["pdf", "csv"])

if uploaded_file is not None:
    analyzer = HustleTaxAnalyzer(phones, banks, names, loans, gambling, pdf_password)

    with st.spinner('Analyzing transactions...'):
        if uploaded_file.name.endswith('.pdf'):
            df, error = analyzer.process_pdf(uploaded_file)
        else:
            df, error = analyzer.process_csv(uploaded_file)

    if error and (df is None or df.empty):
        st.warning(error)

    if df is not None and not df.empty:
        # --- Metrics ---
        taxable_df = df[df['Final_Category'] == 'TAXABLE INCOME']
        taxable_total = taxable_df['Amount'].sum()
        total_in = df[df['Amount'] > 0]['Amount'].sum()

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Money In", f"Ksh {total_in:,.2f}")
        col2.metric("Clean Taxable Income", f"Ksh {taxable_total:,.2f}", delta_color="inverse")

        # Simple Tax Brackets Estimate (KRA 2024 for Individuals - over 288k p.a. approx)
        tax_estimate = "Check Brackets"
        if taxable_total < 24000: # Rough monthly exempt
            tax_estimate = "Ksh 0.00"
        elif taxable_total < 288000: # Rough annual exempt
            tax_estimate = "Below Annual Limit"

        col3.metric("Tax Owed (Estimate)", tax_estimate)

        # --- Visualization ---
        st.subheader("Income Breakdown")
        summary = df[df['Amount'] > 0].groupby('Final_Category')['Amount'].sum()
        if not summary.empty:
            st.bar_chart(summary)
        else:
            st.info("No income found to display in the chart.")

        # --- Data Table ---
        st.subheader("Verified Taxable Entries")
        st.dataframe(taxable_df[['Date', 'Amount', 'Description']], use_container_width=True)

        # --- Download Button ---
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Sanitized Report as CSV",
            data=csv,
            file_name='Sanitized_KRA_Report.csv',
            mime='text/csv',
        )
else:
    st.info("Please upload an M-Pesa statement to begin.")
