#YM用のCharacter.csvをTW用csvにソートするのを補助するスクリプト

import csv
import os

# TWのキャラクターCSVファイルのディレクトリ
tw_csv_dir = 'H:\era\eraTW-SD\CSV\Chara'

# TWのキャラクター情報を辞書として読み込む
tw_characters = {}
for filename in os.listdir(tw_csv_dir):
    if filename.endswith('.csv'):
        with open(os.path.join(tw_csv_dir, filename), 'r', encoding='utf-8-sig') as file:
            reader = csv.reader(file)
            char_name = None
            char_number = None
            for i, row in enumerate(reader):
                if i >= 3:  # 最初の3行だけを読み込む
                    break
                if row[0] == '番号':
                    char_number = row[1]
                elif row[0] == '呼び名':
                    char_name = row[1]
                    print(f"Found name: {char_name}")  # 取得した呼び名を表示
                
                if char_name and char_number:
                    tw_characters[char_name] = char_number
                else:
                    print(f"Warning: Missing data in file {filename}: {row}")

# YMのCSVファイルを読み込む
with open('ym_characters.csv', 'r', encoding='utf-8') as file:
    ym_characters = list(csv.DictReader(file))

# YMのCSVデータにTWの固有番号を追加
for ym_char in ym_characters:
    name = ym_char.get('キャラ名')  # YMのCSVの名前のカラム
    if name is None:
        print(f"Warning: Missing 'キャラ名' in YM data: {ym_char}")
        continue

    tw_id = tw_characters.get(name)
    if tw_id:
        ym_char['tw_id'] = tw_id
    else:
        print(f"Warning: Name '{name}' not found in TW data")

# 新しいCSVファイルとして出力
with open('updated_ym_characters.csv', 'w', newline='', encoding='utf-8') as file:
    writer = csv.DictWriter(file, fieldnames=ym_characters[0].keys())
    writer.writeheader()
    writer.writerows(ym_characters)
