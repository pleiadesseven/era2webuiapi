#ERB\MOVEMENTS\物件関連\PLACE_ERH.ERHからMAPIDと場所IDをCSVにするスクリプト
import pandas as pd
import re

# ERHファイルのパスを指定
erh_path = "H:\era\eraTW-SD\ERB\MOVEMENTS\物件関連\PLACE_ERH.ERH"

# PLACE_ERH.ERH ファイルを読み込む
with open(erh_path, 'r', encoding='utf-8') as file:
    lines = file.readlines()

# MAPIDと場所IDのマッピングを作成するためのリストを初期化
map_ids = {}
place_ids = []
for i, line in enumerate(lines):
    # 13行目までがMAPID
    if i < 13:
        match = re.match(r"#DIM CONST (MAP\w+)\s*=\s*(\d+)", line)
        if match:
            map_name, map_id = match.groups()
            map_ids[int(map_id)] = map_name
    # 17行目以降が場所ID
    elif i >= 17:
        match = re.match(r"#DIM CONST (P\d+\w+)\s*=\s*(\d+)", line)
        if match:
            place_name, place_id = match.groups()
            # 地名から数字と大文字のPを除去
            clean_place_name = re.sub(r'[P\d]+', '', place_name)
            place_ids.append([int(place_id), clean_place_name, map_ids.get(int(place_id) // 100, '')])

# データフレームを作成
df = pd.DataFrame(place_ids, columns=['場所ID', '地名', 'MAPID'])

# CSVに出力
df.to_csv('Generated_Location.csv', index=False)

df.head()  # 最初の数行を表示して内容を確認
