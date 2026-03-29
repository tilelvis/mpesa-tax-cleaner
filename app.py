import streamlit as st
import pypdf
import pandas as pd
import re
import io

class HustleTaxAnalyzer:
    def __init__(self, pdf_file, my_other_numbers, my_banks, password=None):
        self.pdf_file = pdf_file
        # Extract last 3 digits of phone numbers to catch masked IDs like ...554
        self.personal_ids = [str(n).strip()[-3:] for n in my_other_numbers if len(str(n)) >= 3]
        self.bank_keywords = [b.lower().strip() for b in my_banks if b.strip()]
        self.password = password

    def process_statement(self):
        # 1. Extract Text from the uploaded buffer
        text = ""
        try:
            reader = pypdf.PdfReader(self.pdf_file)
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

        # 2. Parse Transactions
        transactions = []
        current_tx = None
        lines = text.split('\n')

        # Regex for M-Pesa Format: Receipt No, Date, Time, and Details
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

        # 3. Categorize
        rows = []
        for tx in transactions:
            det = tx['Details']
            # Search for Status, Amount, and Balance at the end of the string
            # Format: Completed 500.00 1,200.00
            m = re.search(r'(Completed|Failed|Cancelled|Pending)\s+([\d,.-]+)\s+([\d,.-]+)$', det)

            if m:
                status = m.group(1).lower()
                amt_str = m.group(2).replace(',', '')
                try:
                    amt = float(amt_str)
                except ValueError:
                    continue

                content = det[:m.start()].strip().lower()

                # We only care about completed income (positive amounts)
                if status == 'completed' and amt > 0:
                    is_bank = any(bank in content for bank in self.bank_keywords)
                    is_self = any(content.endswith(ide) for ide in self.personal_ids)
                    is_loan = any(loan in content for loan in ['m-shwari', 'fuliza', 'kcb m-pesa', 'loan'])

                    category = 'TAXABLE INCOME'
                    if is_bank: category = 'ASSET TRANSFER (BANK)'
                    elif is_self: category = 'ASSET TRANSFER (MOBILE)'
                    elif is_loan: category = 'LOAN/SAVINGS'

                    rows.append({
                        'Month': tx['Date'][:7],
                        'Date': tx['Date'],
                        'Category': category,
                        'Amount': amt,
                        'Description': content.upper()
                    })

        # Define the structure even if rows is empty to prevent KeyError later
        df = pd.DataFrame(rows, columns=['Month', 'Date', 'Category', 'Amount', 'Description'])
        if df.empty:
            return df, "No relevant income transactions found after filtering."

        return df, None

# --- STREAMLIT UI ---
st.set_page_config(page_title="Hustle Tax Analyzer", page_icon="💰")

st.title("💰 Hustle Tax Analyzer")
st.markdown("""
Upload your M-Pesa statement to filter out bank transfers and loans,
leaving only your **estimated taxable income**.
""")

with st.sidebar:
    st.header("Settings")

    st.info("M-Pesa statements are usually encrypted with your ID or Document Number.")
    pdf_password = st.text_input("PDF Password (if encrypted)", type="password")

    st.divider()

    st.info("Define your accounts to exclude them from 'Taxable Income'.")

    bank_input = st.text_area("Your Bank Names (comma separated)",
                             "kcb, sidian, equity, i&m, co-op, absa, dtb, ncba, family")

    phone_input = st.text_area("Your Other Phone Numbers (comma separated)",
                              "254712345678")

    banks = bank_input.split(",")
    phones = phone_input.split(",")

uploaded_file = st.file_uploader("Choose your M-Pesa Statement (PDF)", type="pdf")

if uploaded_file is not None:
    analyzer = HustleTaxAnalyzer(uploaded_file, phones, banks, pdf_password)

    with st.spinner('Analyzing transactions...'):
        df, error = analyzer.process_statement()

    # We display data if we have it, even if there's a non-critical error (like "No relevant income found")
    if error and (df is None or df.empty):
        st.warning(error)

    if df is not None and not df.empty:
        # --- Metrics ---
        total_income = df[df['Category'] == 'TAXABLE INCOME']['Amount'].sum()
        other_transfers = df[df['Category'] != 'TAXABLE INCOME']['Amount'].sum()

        col1, col2 = st.columns(2)
        col1.metric("Est. Taxable Income", f"KES {total_income:,.2f}")
        col2.metric("Excluded Transfers", f"KES {other_transfers:,.2f}")

        # --- Visualization ---
        st.subheader("Income by Month")
        monthly_data = df[df['Category'] == 'TAXABLE INCOME'].groupby('Month')['Amount'].sum()
        if not monthly_data.empty:
            st.bar_chart(monthly_data)
        else:
            st.info("No taxable income found to display in the chart.")

        # --- Data Table ---
        st.subheader("Detailed Breakdown")
        filter_cat = st.multiselect("Filter Categories",
                                    options=df['Category'].unique(),
                                    default=df['Category'].unique())

        filtered_df = df[df['Category'].isin(filter_cat)]
        st.dataframe(filtered_df, use_container_width=True)

        # --- Download Button ---
        csv = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Report as CSV",
            data=csv,
            file_name='Hustle_Tax_Report.csv',
            mime='text/csv',
        )
else:
    st.info("Please upload a PDF statement to begin.")
