import pandas as pd

# 讀取原本的資料
data = pd.read_csv('ptt_stock_targets.csv')

# 將 00 開頭的股票代號複製一份並去掉 00 開頭
prefix_with_00_stock_targets = data[data['no'].str.startswith('00')]
remove_prefix_00_stock_targets = prefix_with_00_stock_targets.assign(no=data['no'].str[2:])

# 將 0 開頭的股票複製一份並去掉開頭
prefix_with_0_stock_targets = data[data['no'].str.startswith('0') & ~data['no'].str.startswith('00')]
remove_prefix_0_stock_targets = prefix_with_0_stock_targets.assign(no=data['no'].str[1:])

# 將這些接入原本的資料
data = pd.concat([data, remove_prefix_00_stock_targets, remove_prefix_0_stock_targets])

# 將這些資料寫入 CSV 當中
data.to_csv('commands_have_stock.csv', index=False)




