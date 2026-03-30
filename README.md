# 🇰🇪 KRA Mpesa-Tax Sanitizer

Transform your M-Pesa statements into a clear report of your estimated taxable income. This application filters out bank transfers, loans, and other non-taxable transactions to help you manage your taxes.

## ⚠️ Important Disclaimer & Data Privacy

### **1. Data Privacy & Passwords**
* **Local Processing:** This application processes your M-Pesa statements locally in your browser/server session.
* **No Storage:** Your PDF passwords and statement data are **not stored** on any database or shared with third parties. Once the session is closed, the data is wiped.
* **Security:** Avoid uploading statements on public or shared computers.

### **2. Accuracy of Classification**
* **Automated Tool:** This is an AI-assisted categorization tool designed to simplify KRA filing. It uses keyword matching to identify banks, loans, and gambling transactions.
* **User Responsibility:** While the logic is tuned for Kenyan M-Pesa formats, it is **not 100% infallible**.
* **Verification Required:** You are legally responsible for the accuracy of your KRA returns. Please verify the "Taxable Income" list manually before submitting your final return on iTax.

### **3. Not Financial Advice**
* This tool is for analytical purposes only and does not constitute professional tax or legal advice.

## Features

- **Multi-Format Support**: Automatically extracts transaction data from both **M-Pesa PDF statements** and **CSV reports**.
- **PDF Decryption**: Support for password-protected PDF statements (usually your ID or Document Number).
- **Smart Categorization**:
  - **Taxable Income**: Your earnings from various sources.
  - **Asset Transfer (Bank)**: Transfers to and from your bank accounts.
  - **Asset Transfer (Mobile)**: Transfers to and from your other mobile numbers or yourself.
  - **Loan/Credit (Non-Taxable)**: Transactions involving overdrafts, credit, M-Shwari, Fuliza, KCB M-Pesa, Tala, Zenka, etc.
  - **Exempt (Gambling Winnings)**: Transactions with withholding tax already paid (e.g., Sportpesa, Betika).
- **Hustle vs. Noise Analysis**: Advanced metrics dashboard showing "Gross Money In" versus "Net Taxable Base" using the 'Rule of Thumb' logic.
- **Interactive Visualizations**: Dynamic Plotly pie charts and bar charts for source and monthly trend analysis.
- **Interactive iTax Checklist**: A final preparation checklist to ensure data accuracy before filing on itax.kra.go.ke.
- **Educational Insights**: Built-in guides explaining Kenyan tax rules (e.g., the 288k rule and why loans are non-taxable).
- **Customizable Filters**: Exclude specific bank names, phone numbers, and registered names via the sidebar.
- **Data Export**: Download your sanitized audit report as a CSV file for long-term record keeping.

## Getting Started

### Prerequisites

- Python 3.8+
- pip (Python package manager)

### Installation

1. Clone this repository or download the source code.
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the App

Start the Streamlit application by running:
```bash
streamlit run app.py
```

The app will open in your default web browser.

## How to Use

1. **Configure Settings**: Use the sidebar to add your registered names, bank names, and any additional phone numbers you want to exclude from the taxable income calculation.
2. **Upload Statement**: Upload your M-Pesa PDF statement or CSV report into the file uploader.
3. **Analyze Results**: View your total money in, clean taxable income, and tax estimates.
4. **Download Report**: Use the "Download Sanitized Report as CSV" button to save your data for your records or tax filing.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support & Engagement

If you find this tool helpful, please consider:
- ⭐ **Starring** the repository on [GitHub](https://github.com/tilelvis/hustlampesa)
- 🤝 **Engaging** with the repository through issues or pull requests.

*Developed by Elvis Tile.*
