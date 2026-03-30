import unittest
import pandas as pd
import re
from app import HustleTaxAnalyzer
from unittest.mock import MagicMock, patch

class TestHustleTaxAnalyzer(unittest.TestCase):
    def setUp(self):
        self.my_names = ["Test User"]
        self.my_banks = ["KCB", "Equity"]
        self.my_phones = ["123456"]
        self.my_loans = ["M-SHWARI", "FULIZA"]
        self.my_gambling = ["BETIKA", "SPORTPESA"]

    @patch('pypdf.PdfReader')
    def test_process_pdf_parsing(self, mock_pdf_reader):
        # Mock the PDF content
        mock_page = MagicMock()
        # Note: M-Pesa PDF amounts are always listed as positive in the details line.
        # Categorization depends on keywords in the description.
        mock_page.extract_text.return_value = """
        AQ12345678 2023-01-01 10:00:00 Received from JOHN DOE Completed 5,000.00 10,000.00
        BQ12345678 2023-01-02 11:00:00 Pay Bill to KCB BANK Completed 1,000.00 9,000.00
        CQ12345678 2023-01-03 12:00:00 Received from 123456 Completed 2,000.00 11,000.00
        DQ12345678 2023-01-04 13:00:00 M-SHWARI LOAN Received Completed 500.00 11,500.00
        EQ12345678 2023-01-05 14:00:00 Received from SPORTPESA Completed 1,500.00 13,000.00
        FQ12345678 2023-01-06 15:00:00 Sent to JANE DOE Completed 3,000.00 10,000.00
        """
        mock_instance = MagicMock()
        mock_instance.pages = [mock_page]
        mock_instance.is_encrypted = False
        mock_pdf_reader.return_value = mock_instance

        analyzer = HustleTaxAnalyzer(self.my_phones, self.my_banks, self.my_names, self.my_loans, self.my_gambling)
        df, error = analyzer.process_pdf(None)

        self.assertIsNone(error)
        self.assertIsNotNone(df)

        categories = df['Final_Category'].tolist()

        # 1. Received from JOHN DOE -> TAXABLE INCOME
        self.assertIn('TAXABLE INCOME', categories)
        # 2. Pay Bill to KCB BANK -> Personal Expense (Not 'Received')
        # Wait, my logic says if not money_in, return Personal Expense.
        self.assertIn('Personal Expense', categories)
        # 3. Received from 254... -> ASSET TRANSFER (MOBILE)
        self.assertIn('ASSET TRANSFER (MOBILE)', categories)
        # 4. M-SHWARI LOAN -> LOAN/CREDIT
        self.assertIn('LOAN/CREDIT (NON-TAXABLE)', categories)
        # 5. SPORTPESA -> EXEMPT (GAMBLING WINNINGS)
        self.assertIn('EXEMPT (GAMBLING WINNINGS)', categories)
        # 6. Sent to JANE DOE -> Personal Expense
        self.assertEqual(categories[5], 'Personal Expense')

    def test_process_csv_standard(self):
        # Test handling of Paid In / Paid Out columns
        csv_data = io.StringIO("""Receipt No,Completion Time,Details,Transaction Status,Paid In,Paid Out,Balance
GQ12345678,2023-01-01 10:00:00,Received from CLIENT A,Completed,"10,000.00",,10000.00
HQ12345678,2023-01-02 11:00:00,Pay Bill to ELECTRICITY,Completed,,"1,500.00",8500.00
""")
        analyzer = HustleTaxAnalyzer(self.my_phones, self.my_banks, self.my_names, self.my_loans, self.my_gambling)
        df, error = analyzer.process_csv(csv_data)

        self.assertIsNone(error)
        self.assertEqual(len(df), 2)
        self.assertEqual(df.iloc[0]['Final_Category'], 'TAXABLE INCOME')
        self.assertEqual(df.iloc[1]['Final_Category'], 'Personal Expense')
        self.assertEqual(df.iloc[1]['Amount'], -1500.0)

import io
if __name__ == '__main__':
    unittest.main()
