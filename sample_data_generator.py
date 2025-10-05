import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

def generate_sample_inventory_data(num_records=50):
    """生成樣本庫存數據（檔案A）"""
    
    # 產品列表
    articles = [f'A{i:03d}' for i in range(1, 21)]  # A001 到 A020
    descriptions = [f'Product {i}' for i in range(1, 21)]
    sites = [f'S{i:03d}' for i in range(1, 11)]  # S001 到 S010
    rp_types = ['RF', 'ND']
    
    data = []
    for _ in range(num_records):
        article = random.choice(articles)
        description = descriptions[articles.index(article)]
        site = random.choice(sites)
        rp_type = random.choice(rp_types)
        
        # 生成合理範圍的數據
        moq = random.randint(5, 50)
        net_stock = random.randint(0, 500)
        pending_received = random.randint(0, 200)
        safety_stock = random.randint(10, 100)
        last_month_sold = random.randint(0, 1000)
        mtd_sold = random.randint(0, 500)
        
        data.append({
            'Article': article,
            'Article Description': description,
            'RP Type': rp_type,
            'Site': site,
            'MOQ': moq,
            'SaSa Net Stock': net_stock,
            'Pending Received': pending_received,
            'Safety Stock': safety_stock,
            'Last Month Sold Qty': last_month_sold,
            'MTD Sold Qty': mtd_sold
        })
    
    return pd.DataFrame(data)

def generate_sample_promotion_data(num_sku_records=30, num_shop_records=10):
    """生成樣本推廣目標數據（檔案B）"""
    
    # 產品和店鋪列表
    articles = [f'A{i:03d}' for i in range(1, 21)]
    sites = [f'S{i:03d}' for i in range(1, 11)]
    group_nos = [f'G{i:03d}' for i in range(1, 6)]  # G001 到 G005
    target_types = ['HK', 'MO', 'ALL']
    
    # Sheet 1: SKU推廣目標
    sku_data = []
    used_combinations = set()
    
    for _ in range(num_sku_records):
        # 確保Article和Group No.的組合唯一
        while True:
            article = random.choice(articles)
            group_no = random.choice(group_nos)
            combination = (article, group_no)
            if combination not in used_combinations:
                used_combinations.add(combination)
                break
        
        sku_target = random.randint(100, 1000)
        target_type = random.choice(target_types)
        promotion_days = random.randint(14, 45)
        target_cover_days = random.randint(3, 14)
        
        sku_data.append({
            'Group No.': group_no,
            'Article': article,
            'SKU Target': sku_target,
            'Target Type': target_type,
            'Promotion Days': promotion_days,
            'Target Cover Days': target_cover_days
        })
    
    # Sheet 2: 店鋪推廣目標
    shop_data = []
    for site in sites[:num_shop_records]:
        shop_target_hk = random.randint(500, 2000)
        shop_target_mo = random.randint(400, 1800)
        shop_target_all = shop_target_hk + shop_target_mo + random.randint(200, 800)
        
        shop_data.append({
            'Site': site,
            'Shop Target(HK)': shop_target_hk,
            'Shop Target(MO)': shop_target_mo,
            'Shop Target(ALL)': shop_target_all
        })
    
    return pd.DataFrame(sku_data), pd.DataFrame(shop_data)

def generate_edge_case_data():
    """生成邊界條件測試數據"""
    
    # 包含各種邊界條件的數據
    edge_case_inventory = pd.DataFrame({
        'Article': ['EDGE001', 'EDGE002', 'EDGE003', 'EDGE004', 'EDGE005'],
        'Article Description': ['Edge Case 1', 'Edge Case 2', 'Edge Case 3', 'Edge Case 4', 'Edge Case 5'],
        'RP Type': ['RF', 'ND', 'RF', 'ND', 'RF'],
        'Site': ['EDGE01', 'EDGE02', 'EDGE03', 'EDGE04', 'EDGE05'],
        'MOQ': [1, 100, 0, 50, 25],
        'SaSa Net Stock': [-10, 0, 1000, 50000, 150],  # 負值、零值、正常值、大值
        'Pending Received': [0, -5, 200, 1000, 75],
        'Safety Stock': [0, 5, 50, 500, 30],
        'Last Month Sold Qty': [0, 150000, -50, 800, 300],  # 零值、超大值、負值
        'MTD Sold Qty': [25, -25, 0, 600, 200]
    })
    
    edge_case_sku = pd.DataFrame({
        'Group No.': ['EDGE_G1', 'EDGE_G2', 'EDGE_G3'],
        'Article': ['EDGE001', 'EDGE002', 'EDGE003'],
        'SKU Target': [0, 5000, 100],  # 零值、大值、正常值
        'Target Type': ['HK', 'ALL', 'MO'],
        'Promotion Days': [0, 90, 30],  # 零值、大值、正常值
        'Target Cover Days': [1, 30, 7]  # 最小值、大值、正常值
    })
    
    edge_case_shop = pd.DataFrame({
        'Site': ['EDGE01', 'EDGE02', 'EDGE03'],
        'Shop Target(HK)': [0, 5000, 1000],
        'Shop Target(MO)': [100, 0, 800],
        'Shop Target(ALL)': [2000, 10000, 2000]
    })
    
    return edge_case_inventory, edge_case_sku, edge_case_shop

def save_sample_files():
    """保存樣本文件到磁盤"""
    
    # 生成正常數據
    inventory_data = generate_sample_inventory_data(100)
    sku_data, shop_data = generate_sample_promotion_data(50, 10)
    
    # 生成邊界條件數據
    edge_inventory, edge_sku, edge_shop = generate_edge_case_data()
    
    # 保存檔案A（庫存數據）
    inventory_data.to_excel('sample_inventory_data.xlsx', index=False)
    edge_inventory.to_excel('sample_inventory_edge_cases.xlsx', index=False)
    
    # 保存檔案B（推廣目標數據）
    with pd.ExcelWriter('sample_promotion_data.xlsx') as writer:
        sku_data.to_excel(writer, sheet_name='Sheet1', index=False)
        shop_data.to_excel(writer, sheet_name='Sheet2', index=False)
    
    with pd.ExcelWriter('sample_promotion_edge_cases.xlsx') as writer:
        edge_sku.to_excel(writer, sheet_name='Sheet1', index=False)
        edge_shop.to_excel(writer, sheet_name='Sheet2', index=False)
    
    print("樣本文件已生成：")
    print("1. sample_inventory_data.xlsx - 正常庫存數據（100條記錄）")
    print("2. sample_promotion_data.xlsx - 正常推廣目標數據")
    print("3. sample_inventory_edge_cases.xlsx - 邊界條件庫存數據")
    print("4. sample_promotion_edge_cases.xlsx - 邊界條件推廣目標數據")
    print("\n這些文件可用於測試系統功能。")

if __name__ == "__main__":
    save_sample_files()