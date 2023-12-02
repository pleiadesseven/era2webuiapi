#CSVの情報を追加するやつ
import csv

def update_csv(existing_csv_path, new_data_csv_path):
    # 既存のCSVファイルのヘッダーを読み込む
    with open(existing_csv_path, 'r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        header = next(reader, None)

    # 新しいデータを読み込む
    with open(new_data_csv_path, 'r', newline='', encoding='utf-8') as file:
        new_data_reader = csv.reader(file)
        new_data_header = next(new_data_reader, None)
        new_data = [row for row in new_data_reader]

    # 既存のCSVファイルに新しいデータを追加
    with open(existing_csv_path, 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        
        # 新しいデータを追加
        for row in new_data:
            # 新しいデータのカラムが既存のCSVファイルのカラムと一致することを確認
            if set(new_data_header).issubset(set(header)):
                # 新しいデータに不足しているカラムを空欄で埋める
                row_dict = dict(zip(new_data_header, row))
                full_row = [row_dict.get(col, '') for col in header]
                writer.writerow(full_row)
            else:
                print("カラムの不一致があります。")


# 使用例
existing_csv_path = 'H:\era\era2webuitest\Cloth.csv'
csv_file_path = 'H:\era\era2webuitest\ctest.csv'
update_csv(existing_csv_path, csv_file_path)