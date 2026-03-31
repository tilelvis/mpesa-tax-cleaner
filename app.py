import streamlit as st
import pypdf
import pandas as pd
import re
import io
import plotly.express as px

DEFAULT_BANKS = 'im bank, i&m, sidian, kcb, equity, co-op, absa, stanchart, ncba, family, transfer from bank'
DEFAULT_LOANS = 'overdraft, credit, chelete, zenka, tala, branch, m-shwari, fuliza, kcb mpesa, unaitas, advance poa, loan, kcb m-pesa, hustler fund, zash, okash'
DEFAULT_GAMBLING = '1xbet, paystack, betika, sportpesa, odibets, betway, b2c'
DEFAULT_PHONES = '123, 456'
DEFAULT_NAMES = 'Your Name'

class MpesaTaxAnalyzer:
    def __init__(self, my_other_numbers, my_banks, my_names, my_loans, my_gambling, password=None):
        self.personal_ids = [str(n).strip() for n in my_other_numbers if n.strip()]
        self.bank_keywords = [b.lower().strip() for b in my_banks if b.strip()]
        self.personal_names = [n.lower().strip() for n in my_names if n.strip()]
        self.loan_keywords = [l.lower().strip() for l in my_loans if l.strip()]
        self.gambling_keywords = [g.lower().strip() for g in my_gambling if g.strip()]
        self.password = password

    def is_money_in(self, desc):
        desc = desc.lower()
        income_indicators = ['received from', 'transfer from bank', 'm-shwari loan', 'kcb m-pesa loan', 'overdraft']
        return any(ind in desc for ind in income_indicators)

    def classify_transaction(self, desc, amt):
        desc = str(desc).lower()

        if not self.is_money_in(desc):
            return "Personal Expense"

        if any(bank in desc for bank in self.bank_keywords):
            return "ASSET TRANSFER (BANK)"

        if any(loan in desc for loan in self.loan_keywords):
            return "LOAN/CREDIT (NON-TAXABLE)"

        if any(bet in desc for bet in self.gambling_keywords):
            return "EXEMPT (GAMBLING WINNINGS)"

        is_self_id = any(f"******{ide}" in desc or desc.endswith(ide) for ide in self.personal_ids)
        is_self_name = any(name in desc for name in self.personal_names)

        if is_self_id or is_self_name:
            return "ASSET TRANSFER (MOBILE)"

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
            elif current_tx and line:
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
            if 'Details' in df.columns:
                df = df.rename(columns={'Details': 'Description'})
            if 'Completion Time' in df.columns:
                df = df.rename(columns={'Completion Time': 'Date'})

            if 'Paid In' in df.columns and 'Paid Out' in df.columns:
                df['Paid In'] = pd.to_numeric(df['Paid In'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
                df['Paid Out'] = pd.to_numeric(df['Paid Out'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
                df['Amount'] = df['Paid In'] - df['Paid Out']
            elif 'Amount' in df.columns:
                df['Amount'] = pd.to_numeric(df['Amount'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
            else:
                return None, "CSV must contain 'Description' (or 'Details') and 'Amount' (or 'Paid In'/'Paid Out') columns."

            def csv_classify(row):
                if row['Amount'] < 0:
                    return "Personal Expense"
                return self.classify_transaction(row['Description'], row['Amount'])

            df['Final_Category'] = df.apply(csv_classify, axis=1)
            return df, None
        except Exception as e:
            return None, f"Error reading CSV: {e}"

def show_disclaimer():
    with st.expander("⚖️ Professional Disclaimer & Data Privacy Notice", expanded=False):
        st.markdown("""
        ### **1. Data Privacy & Local Processing**
        * **Client-Side Simulation:** This application processes all M-Pesa statement data locally within your browser/server session.
        * **Zero Retention:** Your PDF passwords, financial transactions, and identifiers are **not stored**, cached, or transmitted to any external database. All data is purged upon session termination.
        * **Best Practice:** For maximum security, use this tool on a private device and a secure network.

        ### **2. Analytical Limitation**
        * **Heuristic Classification:** This tool utilizes an AI-assisted heuristic engine to categorize transactions. While it is optimized for the standard Kenyan M-Pesa statement format, it is **not 100% infallible**.
        * **Verification Obligation:** You remain legally responsible for the accuracy of any returns submitted to the Kenya Revenue Authority (KRA). This tool is designed to assist in organization, not to replace professional audit or manual verification.

        ### **3. No Professional Financial Advice**
        * The content, metrics, and estimates provided are for **analytical and educational purposes only**. They do not constitute professional tax, legal, or financial advice. Please consult a certified public accountant (CPA) for complex tax situations.
        """)

def main():
    st.set_page_config(page_title="KRA Mpesa-Tax Sanitizer", page_icon="🇰🇪", layout="wide")
    show_disclaimer()

    with st.expander("🔍 How the Categorization Works"):
        st.write("""
        The **Mpesa-Tax Sanitizer** uses a heuristic engine to classify your M-Pesa inflows into six logical buckets:
        1. **TAXABLE INCOME**: The "Clean" revenue that represents your actual business or freelance earnings.
        2. **ASSET TRANSFER (BANK)**: Movements to and from your own bank accounts (e.g., KCB, Equity).
        3. **ASSET TRANSFER (MOBILE)**: Self-transfers between your own M-Pesa lines.
        4. **LOAN/CREDIT (NON-TAXABLE)**: Liabilities like M-Shwari, Fuliza, or the Hustler Fund.
        5. **EXEMPT (GAMBLING WINNINGS)**: Inflows where withholding tax (20%) is already paid at the source.
        6. **Personal Expense**: Outflows that are not considered business revenue.
        """)

    st.title("🇰🇪 KRA Mpesa-Tax Sanitizer")
    st.markdown("""
    ### **Ready to clean your tax data?**
    Stop paying tax on your own transfers and loans. Upload your M-Pesa statement below to reveal your **Real Taxable Income** in seconds.
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

        st.divider()
        st.markdown("""
        ### 👨‍💻 Developed by Elvis Tile
        If this tool helps you, please consider:
        - ⭐ **Leaving a star** on [GitHub](https://github.com/tilelvis/hustlampesa)
        - 🤝 **Engaging** with the repository

        *Free to use under the MIT License.*
        """)

    uploaded_file = st.file_uploader("📂 Drop your M-Pesa PDF or CSV statement here:", type=["pdf", "csv"])

    if uploaded_file is not None:
        analyzer = MpesaTaxAnalyzer(phones, banks, names, loans, gambling, pdf_password)

        with st.spinner('Analyzing transactions...'):
            if uploaded_file.name.endswith('.pdf'):
                df, error = analyzer.process_pdf(uploaded_file)
            else:
                df, error = analyzer.process_csv(uploaded_file)

        if error and (df is None or df.empty):
            st.warning(error)

        if df is not None and not df.empty:
            # --- Metrics Dashboard ---
            taxable_df = df[df['Final_Category'] == 'TAXABLE INCOME']
            taxable_total = taxable_df['Amount'].sum()
            total_in = df[df['Amount'] > 0]['Amount'].sum()
            noise_amount = total_in - taxable_total

            st.subheader("🚀 Your 2025 M-Pesa Snapshot")
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Total Money In", f"Ksh {total_in:,.0f}", help="Every cent that hit your M-Pesa.")
                st.caption("📂 The 'Gross' Figure")

            with col2:
                st.metric("The 'Noise'", f"Ksh {noise_amount:,.0f}", delta="Non-Taxable", delta_color="normal", help="Money that doesn't count as income (Transfers, Loans, etc.)")
                st.caption("🛡️ Non-Taxable Asset Protection")

            with col3:
                reduction = 0
                if total_in > 0:
                    reduction = (noise_amount / total_in) * 100
                st.metric("Real Taxable Income", f"Ksh {taxable_total:,.0f}", delta=f"-{reduction:.0f}% from Gross", delta_color="inverse", help="The portion KRA considers taxable.")
                st.caption("💰 Net Taxable Base (Estimate)")

            # --- Learning Path ---
            st.divider()
            with st.expander("🎓 Learn the 'Rule of Thumb' while you file"):
                st.info("""
                **1. The 288k Rule:** In Kenya, the first **Ksh 288,000** you earn annually is tax-free. If your 'Real Taxable Income' card is low (below 24k/month), you may owe **NIL** tax!

                **2. Debt != Wealth:** Loans (like M-Shwari, Fuliza, or Zenka) are 'Money In' but **not** income. We've automatically identified and filtered them for you.

                **3. The Paper Trail:** KRA requires evidence for audits. Download the 'Sanitized Report' below to document why large bank movements were excluded from your taxable income.
                """)

            # --- Visualizations ---
            c1, c2 = st.columns([1, 1])

            with c1:
                st.subheader("Where did your money come from?")
                pie_data = df[df['Amount'] > 0].groupby('Final_Category')['Amount'].sum().reset_index()
                if not pie_data.empty:
                    fig = px.pie(
                        pie_data,
                        values='Amount',
                        names='Final_Category',
                        hole=0.4,
                        color_discrete_sequence=px.colors.qualitative.Pastel
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No inflow data found for the chart.")

            with c2:
                st.subheader("Monthly Income Trend")
                if 'Date' in df.columns:
                    df['Month'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m')
                    monthly_data = taxable_df.copy()
                    monthly_data['Month'] = pd.to_datetime(monthly_data['Date']).dt.strftime('%Y-%m')
                    monthly_summary = monthly_data.groupby('Month')['Amount'].sum()
                    if not monthly_summary.empty:
                        st.bar_chart(monthly_summary)
                    else:
                        st.info("Insufficient data for monthly trends.")

            # --- Data Table ---
            st.subheader("Verified Taxable Entries")
            st.dataframe(taxable_df[['Date', 'Amount', 'Description']], use_container_width=True)

            # --- Final Prep Checklist ---
            st.divider()
            st.write("### ✅ Final Prep for iTax")
            check1 = st.checkbox("I have confirmed all 'Taxable Income' entries are real business revenue.")
            check2 = st.checkbox("I have verified that 'Asset Transfers' are just me moving my own money.")
            check3 = st.checkbox("I've downloaded my Audit Report for my 5-year records.")

            if check1 and check2 and check3:
                st.balloons()
                st.success("🎉 You are ready to file! Head over to [itax.kra.go.ke](https://itax.kra.go.ke) and enter your 'Real Taxable Income' total.")

            # --- Download Button ---
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Sanitized Audit Report (CSV)",
                data=csv,
                file_name='Sanitized_KRA_Audit_Report.csv',
                mime='text/csv',
            )
    else:
        st.info("👋 **Welcome!** Please upload a PDF or CSV statement to begin your analysis.")

if __name__ == "__main__":
    main()
