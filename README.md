# 💰 Hustle Tax Analyzer

Transform your M-Pesa statements into a clear report of your estimated taxable income. This application filters out bank transfers, loans, and other non-taxable transactions to help you manage your taxes.

## Features

- **PDF Parsing**: Automatically extracts transaction data from standard M-Pesa statement PDFs.
- **Smart Categorization**:
  - **Taxable Income**: Your earnings from various sources.
  - **Asset Transfer (Bank)**: Transfers to and from your bank accounts.
  - **Asset Transfer (Mobile)**: Transfers to and from your other mobile numbers.
  - **Loan/Savings**: Transactions involving M-Shwari, Fuliza, KCB M-Pesa, etc.
- **Interactive Visualizations**: Monthly income trends displayed in a bar chart.
- **Customizable Filters**: Exclude specific bank names and phone numbers via the sidebar.
- **Data Export**: Download your filtered transaction report as a CSV file.

## Getting Started

### Prerequisites

- Python 3.7+
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

1. **Configure Settings**: Use the sidebar to add your bank names and any additional phone numbers you want to exclude from the taxable income calculation.
2. **Upload Statement**: Drag and drop your M-Pesa PDF statement into the file uploader.
3. **Analyze Results**: View your total estimated taxable income, excluded transfers, and monthly trends.
4. **Download Report**: Use the "Download Report as CSV" button to save your data for your records or tax filing.

## Note on Privacy

This application processes your PDF locally in your browser/server and does not store your financial data. Ensure you are running it in a secure environment.
