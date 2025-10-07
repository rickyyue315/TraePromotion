import unittest
import pandas as pd
import numpy as np
from datetime import datetime
import sys
import os

# 將app.py所在的目錄添加到Python路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 導入app.py中的函數
from app import (
    validate_inventory_file, validate_file_b, preprocess_data, 
    calculate_business_logic, create_visualizations, export_to_excel
)

class TestRetailPromotionSystem(unittest.TestCase):
    """零售推廣系統的單元測試"""
    
    def setUp(self):
        """設置測試數據"""
        # 創建有效的檔案A數據
        self.valid_inventory_data = pd.DataFrame({
            'Article': ['A001', 'A002', 'A003'],
            'Article Description': ['Product 1', 'Product 2', 'Product 3'],
            'RP Type': ['RF', 'ND', 'RF'],
            'Site': ['S001', 'S002', 'S003'],
            'MOQ': [10, 20, 15],
            'SaSa Net Stock': [100, 200, 150],
            'Pending Received': [50, 30, 40],
            'Safety Stock': [25, 35, 30],
            'Last Month Sold Qty': [200, 300, 250],
            'MTD Sold Qty': [150, 200, 175],
            'Supply source': ['1', '2', '4'],
            'Description p. group': ['Buyer A', 'Buyer B', 'Buyer C']
        })
        
        # 創建有效的檔案B Sheet1數據
        self.valid_promotion_sku_data = pd.DataFrame({
            'Group No.': ['G001', 'G002', 'G003'],
            'Article': ['A001', 'A002', 'A003'],
            'SKU Target': [500, 600, 700],
            'Target Type': ['HK', 'MO', 'ALL'],
            'Promotion Days': [30, 30, 30],
            'Target Cover Days': [7, 7, 7],
            'Supply source': ['1', '2', '4']
        })
        
        # 創建有效的檔案B Sheet2數據
        self.valid_promotion_shop_data = pd.DataFrame({
            'Site': ['S001', 'S002', 'S003'],
            'Shop Target(HK)': [1000, 1200, 1100],
            'Shop Target(MO)': [800, 900, 850],
            'Shop Target(ALL)': [1800, 2100, 1950],
            'Supply source': ['1', '2', '4']
        })
        
        # 創建包含邊界條件的數據
        self.edge_case_data = pd.DataFrame({
            'Article': ['A001', 'A002', 'A003'],
            'Article Description': ['Product 1', 'Product 2', 'Product 3'],
            'RP Type': ['RF', 'ND', 'RF'],
            'Site': ['S001', 'S002', 'S003'],
            'MOQ': [10, 20, 15],
            'SaSa Net Stock': [-50, 0, 150000],  # 負值、零值、異常大值
            'Pending Received': [50, -30, 40],
            'Safety Stock': [25, 35, 30],
            'Last Month Sold Qty': [200000, 0, -100],  # 異常大值、零值、負值
            'MTD Sold Qty': [150, -50, 300000],
            'Supply source': ['1', 'invalid', '2'],  # 包含無效來源
            'Description p. group': ['Buyer A', '', 'Buyer C']  # 包含空值
        })
        
        # 創建缺失欄位的數據
        self.missing_fields_data = pd.DataFrame({
            'Article': ['A001', 'A002'],
            'Article Description': ['Product 1', 'Product 2'],
            # 缺少其他必需欄位
        })
        
        # 創建缺貨情況的數據
        self.out_of_stock_data = pd.DataFrame({
            'Article': ['A001', 'A002', 'A003'],
            'Article Description': ['Product 1', 'Product 2', 'Product 3'],
            'RP Type': ['RF', 'ND', 'RF'],
            'Site': ['S001', 'S002', 'S003'],
            'MOQ': [10, 20, 15],
            'SaSa Net Stock': [0, 5, 0],  # 缺貨情況
            'Pending Received': [0, 10, 5],
            'Safety Stock': [25, 40, 30],
            'Last Month Sold Qty': [300, 450, 600],
            'MTD Sold Qty': [100, 150, 200],
            'Supply source': ['1', '2', '4'],  # 不同補貨來源
            'Description p. group': ['Buyer A', 'RP Team', 'Buyer C']
        })
        
        # 創建無效補貨來源的數據
        self.invalid_supply_source_data = pd.DataFrame({
            'Article': ['A001', 'A002'],
            'Article Description': ['Product 1', 'Product 2'],
            'RP Type': ['RF', 'RF'],
            'Site': ['S001', 'S002'],
            'MOQ': [10, 20],
            'SaSa Net Stock': [50, 75],
            'Pending Received': [25, 30],
            'Safety Stock': [25, 40],
            'Last Month Sold Qty': [300, 450],
            'MTD Sold Qty': [100, 150],
            'Supply source': ['invalid', ''],  # 無效和空的補貨來源
            'Description p. group': ['Buyer A', 'Buyer B']
        })
    
    def test_validate_file_a_valid(self):
        """測試有效的檔案A驗證"""
        missing_cols = validate_inventory_file(self.valid_inventory_data)
        self.assertEqual(len(missing_cols), 0, "Valid file A should have no missing columns")
    
    def test_validate_file_a_missing_fields(self):
        """測試檔案A缺失欄位的驗證"""
        missing_cols = validate_inventory_file(self.missing_fields_data)
        self.assertGreater(len(missing_cols), 0, "Missing fields should be detected")
        expected_missing = ['RP Type', 'Site', 'MOQ', 'SaSa Net Stock', 'Pending Received', 
                           'Safety Stock', 'Last Month Sold Qty', 'MTD Sold Qty', 
                           'Supply source', 'Description p. group']
        for col in expected_missing:
            self.assertIn(col, missing_cols, f"Missing column {col} should be detected")
    
    def test_validate_file_b_valid(self):
        """測試有效的檔案B驗證"""
        missing_sheet1, missing_sheet2 = validate_file_b(
            self.valid_promotion_sku_data, self.valid_promotion_shop_data
        )
        self.assertEqual(len(missing_sheet1), 0, "Valid sheet 1 should have no missing columns")
        self.assertEqual(len(missing_sheet2), 0, "Valid sheet 2 should have no missing columns")
    
    def test_preprocess_data_normalization(self):
        """測試數據預處理的正常化"""
        processed_data = preprocess_data(self.valid_inventory_data)
        
        # 檢查Article欄位是否被正確處理為字串
        self.assertTrue(all(isinstance(x, str) for x in processed_data['Article']))
        
        # 檢查數值欄位是否為數值類型
        numeric_cols = ['MOQ', 'SaSa Net Stock', 'Pending Received', 'Safety Stock',
                       'Last Month Sold Qty', 'MTD Sold Qty']
        for col in numeric_cols:
            self.assertTrue(pd.api.types.is_numeric_dtype(processed_data[col]), 
                          f"Column {col} should be numeric after preprocessing")
    
    def test_preprocess_data_edge_cases(self):
        """測試數據預處理的邊界條件處理"""
        processed_data = preprocess_data(self.edge_case_data)
        
        # 檢查負值是否被修正為0
        self.assertGreaterEqual(processed_data.loc[0, 'SaSa Net Stock'], 0, 
                               "Negative stock values should be corrected to 0")
        
        # 檢查異常大值是否被限制
        self.assertLessEqual(processed_data.loc[2, 'Last Month Sold Qty'], 100000, 
                           "Abnormally large sales values should be capped at 100000")
        
        # 檢查Notes欄位是否被添加
        self.assertIn('Notes', processed_data.columns, "Notes column should be added")
        self.assertTrue(len(processed_data['Notes'].iloc[0]) > 0, "Notes should contain correction information")
        
        # 檢查補貨來源處理
        self.assertEqual(processed_data.loc[0, 'Supply source'], '1', "Valid supply source should be preserved")
        self.assertEqual(processed_data.loc[1, 'Supply source'], '無效來源', "Invalid supply source should default to '無效來源'")
        self.assertEqual(processed_data.loc[2, 'Supply source'], '2', "Valid supply source should be preserved")
        
        # 檢查買家組別處理
        self.assertEqual(processed_data.loc[1, 'Description p. group'], '', "Empty buyer group should default to empty string")
    
    def test_business_logic_calculation(self):
        """測試核心業務邏輯計算"""
        # 預處理數據
        inventory_processed = preprocess_data(self.valid_inventory_data)
        promotion_sku_processed = preprocess_data(self.valid_promotion_sku_data)
        promotion_shop_processed = preprocess_data(self.valid_promotion_shop_data)
        
        # 執行計算
        results, message = calculate_business_logic(
            inventory_processed, promotion_sku_processed, promotion_shop_processed
        )
        
        # 驗證結果
        self.assertFalse(results.empty, "Calculation should produce non-empty results")
        self.assertIn('Daily Sales Rate', results.columns, "Daily Sales Rate should be calculated")
        self.assertIn('Total Demand', results.columns, "Total Demand should be calculated")
        self.assertIn('Net Demand', results.columns, "Net Demand should be calculated")
        self.assertIn('Suggested Dispatch Qty', results.columns, "Suggested Dispatch Qty should be calculated")
        self.assertIn('Out of Stock Qty', results.columns, "Out of Stock Qty should be calculated")
        self.assertIn('Notification Notes', results.columns, "Notification Notes should be calculated")
        self.assertIn('Supply source', results.columns, "Supply source should be preserved")
        self.assertIn('Description p. group', results.columns, "Description p. group should be preserved")
        
        # 驗證計算邏輯
        self.assertTrue(all(results['Daily Sales Rate'] >= 0), "Daily sales rate should be non-negative")
        self.assertTrue(all(results['Total Demand'] >= 0), "Total demand should be non-negative")
        self.assertTrue(all(results['Net Demand'] >= 0), "Net demand should be non-negative")
        self.assertTrue(all(results['Out of Stock Qty'] >= 0), "Out of stock qty should be non-negative")
        
        # 驗證派貨建議邏輯
        rf_mask = results['RP Type'] == 'RF'
        nd_mask = results['RP Type'] == 'ND'
        
        self.assertTrue(all(results.loc[nd_mask, 'Suggested Dispatch Qty'] == 0), 
                       "ND items should have 0 suggested dispatch")
        self.assertTrue(all(results.loc[rf_mask, 'Suggested Dispatch Qty'] >= results.loc[rf_mask, 'MOQ']), 
                       "RF items should have suggested dispatch >= MOQ")
    
    def test_business_logic_empty_data(self):
        """測試空數據的業務邏輯處理"""
        empty_df = pd.DataFrame()
        
        results, message = calculate_business_logic(empty_df, empty_df, empty_df)
        
        self.assertTrue(results.empty, "Empty input should produce empty results")
        self.assertIn("No valid data", message, "Should return appropriate message for empty data")
    
    def test_business_logic_division_by_zero(self):
        """測試除零情況的處理"""
        # 創建銷量為零的數據
        zero_sales_data = self.valid_inventory_data.copy()
        zero_sales_data['Last Month Sold Qty'] = 0
        zero_sales_data['MTD Sold Qty'] = 0
        
        inventory_processed = preprocess_data(zero_sales_data)
        promotion_sku_processed = preprocess_data(self.valid_promotion_sku_data)
        promotion_shop_processed = preprocess_data(self.valid_promotion_shop_data)
        
        results, message = calculate_business_logic(
            inventory_processed, promotion_sku_processed, promotion_shop_processed
        )
        
        self.assertFalse(results.empty, "Should handle zero sales without error")
        self.assertTrue(all(results['Daily Sales Rate'] == 0), "Daily sales rate should be 0 when no sales")
    
    def test_export_functionality(self):
        """測試匯出功能"""
        # 預處理數據並執行計算
        inventory_processed = preprocess_data(self.valid_inventory_data)
        promotion_sku_processed = preprocess_data(self.valid_promotion_sku_data)
        promotion_shop_processed = preprocess_data(self.valid_promotion_shop_data)
        
        results, _ = calculate_business_logic(
            inventory_processed, promotion_sku_processed, promotion_shop_processed
        )
        
        # 創建摘要數據
        summary_data = results.groupby(['Group No.', 'Site', 'Supply source']).agg({
            'Total Demand': 'sum',
            'Available Stock': 'sum',
            'Suggested Dispatch Qty': 'sum',
            'Out of Stock Qty': 'sum'
        }).reset_index()
        
        # 測試匯出
        excel_file = export_to_excel(results, summary_data)
        
        self.assertIsNotNone(excel_file, "Excel export should not be None")
        self.assertGreater(len(excel_file.getvalue()), 0, "Excel file should have content")
        
        # 驗證Excel內容
        excel_data = pd.read_excel(excel_file, sheet_name='Analysis Results')
        self.assertEqual(len(excel_data), len(results), "Exported data should match original results")
    
    def test_data_types_after_preprocessing(self):
        """測試預處理後的數據類型"""
        processed_data = preprocess_data(self.valid_inventory_data)
        
        # 檢查字串欄位
        string_cols = ['Article', 'Article Description', 'RP Type', 'Site']
        for col in string_cols:
            self.assertTrue(all(isinstance(x, str) for x in processed_data[col]), 
                          f"Column {col} should be string type after preprocessing")
        
        # 檢查數值欄位
        numeric_cols = ['MOQ', 'SaSa Net Stock', 'Pending Received', 'Safety Stock',
                       'Last Month Sold Qty', 'MTD Sold Qty']
        for col in numeric_cols:
            self.assertTrue(pd.api.types.is_numeric_dtype(processed_data[col]), 
                          f"Column {col} should be numeric type after preprocessing")
    
    def test_calculation_consistency(self):
        """測試計算的一致性"""
        # 預處理數據
        inventory_processed = preprocess_data(self.valid_inventory_data)
        promotion_sku_processed = preprocess_data(self.valid_promotion_sku_data)
        promotion_shop_processed = preprocess_data(self.valid_promotion_shop_data)
        
        # 多次執行計算
        results1, _ = calculate_business_logic(
            inventory_processed, promotion_sku_processed, promotion_shop_processed
        )
        results2, _ = calculate_business_logic(
            inventory_processed, promotion_sku_processed, promotion_shop_processed
        )
        
        # 驗證結果一致性
        pd.testing.assert_frame_equal(results1, results2, 
                                    "Multiple calculations should produce identical results")
    
    def test_out_of_stock_calculation(self):
        """測試缺貨計算邏輯"""
        # 預處理缺貨數據
        inventory_processed = preprocess_data(self.out_of_stock_data)
        promotion_sku_processed = preprocess_data(self.valid_promotion_sku_data)
        promotion_shop_processed = preprocess_data(self.valid_promotion_shop_data)
        
        # 執行計算
        results, message = calculate_business_logic(
            inventory_processed, promotion_sku_processed, promotion_shop_processed
        )
        
        # 驗證缺貨數量計算
        self.assertFalse(results.empty, "Calculation should produce non-empty results")
        self.assertIn('Out of Stock Qty', results.columns, "Out of Stock Qty should be calculated")
        
        # 檢查缺貨項目
        out_of_stock_items = results[results['Out of Stock Qty'] > 0]
        self.assertGreater(len(out_of_stock_items), 0, "Should detect out of stock items")
        
        # 檢查通知邏輯
        buyer_notification_items = results[
            (results['Supply source'].isin(['1', '4'])) & 
            (results['Out of Stock Qty'] > 0)
        ]
        rp_team_items = results[
            (results['Supply source'] == '2') & 
            (results['Out of Stock Qty'] > 0)
        ]
        
        if len(buyer_notification_items) > 0:
            self.assertTrue(
                any('缺貨通知：Buyer' in str(note) for note in buyer_notification_items['Notification Notes']),
                "Buyer notification should be added for supply sources 1 and 4"
            )
        
        if len(rp_team_items) > 0:
            self.assertTrue(
                any('RP team建議' in str(note) for note in rp_team_items['Notification Notes']),
                "RP team suggestion should be added for supply source 2"
            )
    
    def test_invalid_supply_source_handling(self):
        """測試無效補貨來源的處理"""
        # 預處理數據
        inventory_processed = preprocess_data(self.invalid_supply_source_data)
        promotion_sku_processed = preprocess_data(self.valid_promotion_sku_data)
        promotion_shop_processed = preprocess_data(self.valid_promotion_shop_data)
        
        # 執行計算
        results, message = calculate_business_logic(
            inventory_processed, promotion_sku_processed, promotion_shop_processed
        )
        
        # 驗證無效補貨來源被替換為預設值
        self.assertEqual(results.loc[0, 'Supply source'], '無效來源', 
                        "Invalid supply source should be replaced with '無效來源'")
        self.assertEqual(results.loc[1, 'Supply source'], '無效來源', 
                        "Empty supply source should be replaced with '無效來源'")
    
    def test_data_types_with_new_fields(self):
        """測試包含新欄位的數據類型"""
        processed_data = preprocess_data(self.valid_inventory_data)
        
        # 檢查新欄位的數據類型
        self.assertTrue(all(isinstance(x, str) for x in processed_data['Supply source']), 
                       "Supply source should be string type")
        self.assertTrue(all(isinstance(x, str) for x in processed_data['Description p. group']), 
                       "Description p. group should be string type")
        
        # 檢查新欄位是否存在
        self.assertIn('Supply source', processed_data.columns, "Supply source column should exist")
        self.assertIn('Description p. group', processed_data.columns, "Description p. group column should exist")

if __name__ == '__main__':
    # 創建測試套件
    suite = unittest.TestLoader().loadTestsFromTestCase(TestRetailPromotionSystem)
    
    # 運行測試
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 輸出測試結果
    if result.wasSuccessful():
        print("\n✅ All tests passed successfully!")
    else:
        print(f"\n❌ {len(result.failures)} test(s) failed, {len(result.errors)} error(s)")
        
        if result.failures:
            print("\nFailures:")
            for test, traceback in result.failures:
                print(f"- {test}: {traceback}")
        
        if result.errors:
            print("\nErrors:")
            for test, traceback in result.errors:
                print(f"- {test}: {traceback}")
    
    # 返回退出碼（供CI/CD使用）
    exit(0 if result.wasSuccessful() else 1)