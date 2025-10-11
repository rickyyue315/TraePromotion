import unittest
import pandas as pd
from app import load_data, calculate_demand

class TestApp(unittest.TestCase):

    def test_column_validation(self):
        # 創建一個缺少必要欄位的 DataFrame
        data_a = {'Article': ['A1'], 'Site': ['S1']}
        df_a = pd.DataFrame(data_a)
        
        # 創建一個有效的 DataFrame B
        data_b1 = {'Group No.': ['G1'], 'Article': ['A1'], 'SKU Target': [10], 'Target Type': ['HK'], 'Promotion Days': [7], 'Target Cover Days': [14]}
        df_b1 = pd.DataFrame(data_b1)
        data_b2 = {'Site': ['S1'], 'Shop Target(HK)': [0.1], 'Shop Target(MO)': [0], 'Shop Target(ALL)': [0]}
        df_b2 = pd.DataFrame(data_b2)

        # 寫入到 BytesIO
        from io import BytesIO
        file_a = BytesIO()
        df_a.to_excel(file_a, index=False)
        file_a.seek(0)

        file_b = BytesIO()
        with pd.ExcelWriter(file_b, engine='openpyxl') as writer:
            df_b1.to_excel(writer, sheet_name='Sheet1', index=False)
            df_b2.to_excel(writer, sheet_name='Sheet2', index=False)
        file_b.seek(0)

        # 由於 load_data 函數中的 st.error 會中止程序，我們預期它會返回 None
        result, _ = load_data(file_a, file_b)
        self.assertIsNone(result)

    def test_negative_value_correction(self):
        # 創建包含負值的數據
        data_a = {'Article': ['A1'], 'Article Description': ['Desc1'], 'RP Type': ['RF'], 'Site': ['S1'], 'MOQ': [10], 'SaSa Net Stock': [-5], 'Pending Received': [0], 'Safety Stock': [0], 'Last Month Sold Qty': [30], 'MTD Sold Qty': [15], 'Supply source': [2], 'Description p. group': ['Buyer1']}
        df_a = pd.DataFrame(data_a)
        
        data_b1 = {'Group No.': ['G1'], 'Article': ['A1'], 'SKU Target': [10], 'Target Type': ['HK'], 'Promotion Days': [7], 'Target Cover Days': [14]}
        df_b1 = pd.DataFrame(data_b1)
        data_b2 = {'Site': ['S1'], 'Shop Target(HK)': [0.1], 'Shop Target(MO)': [0], 'Shop Target(ALL)': [0]}
        df_b2 = pd.DataFrame(data_b2)

        from io import BytesIO
        file_a = BytesIO()
        df_a.to_excel(file_a, index=False)
        file_a.seek(0)

        file_b = BytesIO()
        with pd.ExcelWriter(file_b, engine='openpyxl') as writer:
            df_b1.to_excel(writer, sheet_name='Sheet1', index=False)
            df_b2.to_excel(writer, sheet_name='Sheet2', index=False)
        file_b.seek(0)

        result, _ = load_data(file_a, file_b)
        self.assertEqual(result['SaSa Net Stock'].iloc[0], 0)

    def test_sales_truncation(self):
        # 創建銷量異常的數據
        data_a = {'Article': ['A1'], 'Article Description': ['Desc1'], 'RP Type': ['RF'], 'Site': ['S1'], 'MOQ': [10], 'SaSa Net Stock': [10], 'Pending Received': [0], 'Safety Stock': [0], 'Last Month Sold Qty': [150000], 'MTD Sold Qty': [15], 'Supply source': [2], 'Description p. group': ['Buyer1']}
        df_a = pd.DataFrame(data_a)

        data_b1 = {'Group No.': ['G1'], 'Article': ['A1'], 'SKU Target': [10], 'Target Type': ['HK'], 'Promotion Days': [7], 'Target Cover Days': [14]}
        df_b1 = pd.DataFrame(data_b1)
        data_b2 = {'Site': ['S1'], 'Shop Target(HK)': [0.1], 'Shop Target(MO)': [0], 'Shop Target(ALL)': [0]}
        df_b2 = pd.DataFrame(data_b2)

        from io import BytesIO
        file_a = BytesIO()
        df_a.to_excel(file_a, index=False)
        file_a.seek(0)

        file_b = BytesIO()
        with pd.ExcelWriter(file_b, engine='openpyxl') as writer:
            df_b1.to_excel(writer, sheet_name='Sheet1', index=False)
            df_b2.to_excel(writer, sheet_name='Sheet2', index=False)
        file_b.seek(0)

        result, _ = load_data(file_a, file_b)
        self.assertEqual(result['Last Month Sold Qty'].iloc[0], 100000)

    def test_merge_logic(self):
        # 創建用於測試合併的數據
        data_a = {'Article': ['A1', 'A2'], 'Site': ['S1', 'S2'], 'Article Description': ['Desc1', 'Desc2'], 'RP Type': ['RF', 'RF'], 'MOQ': [10, 10], 'SaSa Net Stock': [10, 10], 'Pending Received': [0, 0], 'Safety Stock': [0, 0], 'Last Month Sold Qty': [30, 60], 'MTD Sold Qty': [15, 30], 'Supply source': [2, 2], 'Description p. group': ['Buyer1', 'Buyer2']}
        df_a = pd.DataFrame(data_a)

        data_b1 = {'Group No.': ['G1'], 'Article': ['A1'], 'SKU Target': [10], 'Target Type': ['HK'], 'Promotion Days': [7], 'Target Cover Days': [14]}
        df_b1 = pd.DataFrame(data_b1)
        data_b2 = {'Site': ['S1'], 'Shop Target(HK)': [0.1], 'Shop Target(MO)': [0], 'Shop Target(ALL)': [0]}
        df_b2 = pd.DataFrame(data_b2)

        from io import BytesIO
        file_a = BytesIO()
        df_a.to_excel(file_a, index=False)
        file_a.seek(0)

        file_b = BytesIO()
        with pd.ExcelWriter(file_b, engine='openpyxl') as writer:
            df_b1.to_excel(writer, sheet_name='Sheet1', index=False)
            df_b2.to_excel(writer, sheet_name='Sheet2', index=False)
        file_b.seek(0)

        result, _ = load_data(file_a, file_b)
        self.assertEqual(len(result), 2)
        self.assertEqual(result.loc[result['Article'] == 'A1', 'Group No.'].iloc[0], 'G1')
        self.assertTrue(pd.isna(result.loc[result['Article'] == 'A2', 'Group No.'].iloc[0]) or result.loc[result['Article'] == 'A2', 'Group No.'].iloc[0] == '')


    def test_calculation_accuracy(self):
        # 創建一組用於手動驗證的數據
        data = {'Article': ['A1'], 'Site': ['S1'], 'Last Month Sold Qty': [30], 'Target Cover Days': [14], 'SKU Target': [100], 'Target Type': ['HK'], 'Shop Target(HK)': [0.5], 'SaSa Net Stock': [5], 'Pending Received': [2], 'Safety Stock': [3], 'RP Type': ['RF'], 'MOQ': [10], 'Supply source': [2], 'Group No.': ['G1']}
        df = pd.DataFrame(data)
        
        # 手動計算預期結果
        # Daily Sales Rate = 30 / 30 = 1
        # Regular Demand = 1 * (14 + 2) = 16 (Lead Time = 2)
        # Promo Demand = 100 * 0.5 = 50
        # Total Demand = 16 + 50 = 66
        # Net Demand = 66 - (5 + 2) + 3 = 62
        # Suggested Dispatch Qty = max(62, 10) = 62
        
        result, _ = calculate_demand(df, lead_time=2)
        
        self.assertAlmostEqual(result['Daily Sales Rate'].iloc[0], 1.0)
        self.assertAlmostEqual(result['Regular Demand'].iloc[0], 16.0)
        self.assertAlmostEqual(result['Promo Demand'].iloc[0], 50.0)
        self.assertAlmostEqual(result['Total Demand'].iloc[0], 66.0)
        self.assertAlmostEqual(result['Net Demand'].iloc[0], 62.0)
        self.assertEqual(result['Suggested Dispatch Qty'].iloc[0], 62)
        self.assertEqual(result['Dispatch Type'].iloc[0], '需生成 DN')

if __name__ == '__main__':
    unittest.main()