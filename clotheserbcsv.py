#ERB\OBJ\CLASS\CLOTHES をCSVにするやつ
import csv
import os
import re



# EBRファイルの最初の行からキーワードを抽出する関数
def extract_keyword(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        first_line = file.readline().strip()
        return first_line.lstrip(';')



def extract_data_from_ebr(file_path, keyword):
    extracted_data = {}
    
    escaped_keyword = re.escape(keyword)
    pattern = re.compile(
        rf'@{escaped_keyword}(?P<number>\d+)\(ARG, O_DATA, V_NAME\)\s*'
        rf'#FUNCTION\s*'
        rf'#LOCALSIZE 1\s*'
        rf'#LOCALSSIZE 1\s*'
        rf'#DIMS O_DATA\s*'
        rf'#DIMS V_NAME\s*'
        rf'SELECTCASE O_DATA\s*'
        rf'CASE "名前"\s*'
        rf'\tCALLF MAKE_STR\(V_NAME, "(?P<name>[^"]+)"\)\s*'
        rf'CASE "装備部位"\s*'
        rf'CALLF MAKE_STR\(V_NAME, "「(?P<position>[^「」]+)」"\)'
    )
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()  # ファイル全体を読み込む
        for match in pattern.finditer(content):
            #numはint型指定しないと {'1': {'カテゴリ内番号': '1', '衣類名': '眼鏡', '装備部位': '「アクセサリ」'} こうなってしまう
            number = match.group('number')
            name = match.group('name')
            position = match.group('position')
            #print(f"keyword {keyword} Extracted Data - Number: {number}, Name: {name}, Position: {position}")  # 抽出したデータを表示
            extracted_data[number] = {'カテゴリ内番号': number, '衣類名': name, '装備部位': position}
    return extracted_data


def append_to_csv(csv_file_path, extracted_data, required_columns):
    with open(csv_file_path, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        for data in extracted_data.values():
            row = []
            for col in required_columns:
                print(f"extracted_data:{extracted_data}")
                row.append(data.get(col, ''))  # 対応するキーの値を取得、なければ空文字を追加
            writer.writerow(row)


erb_folder = 'H:\era\era2webuitest\eraTW-SD\ERB\OBJ\CLASS\CLOTHES'
csv_file_path = 'H:\era\era2webuitest\ctest.csv'
required_columns = ['カテゴリ内番号', '衣類名', '装備部位']
for file_name in os.listdir(erb_folder):
    if file_name.startswith('CLOTHES_') and file_name.endswith('.ERB'):
        keyword_match = re.search(r'CLOTHES_(\w+).ERB', file_name)
        if keyword_match:
            keyword = keyword_match.group(1)
            file_path = os.path.join(erb_folder, file_name)
            extracted_data = extract_data_from_ebr(file_path, keyword)
            # print(f"extracted_data:{extracted_data}")
            # # 抽出したデータを表示
            # print(f"Extracted data from file: {file_name}")
            # for number, data in extracted_data.items():
            #     print(f" {number}, {data['衣類名']}, {data['装備部位']}")
            
            # CSVファイルにデータを追加
            append_to_csv(csv_file_path, extracted_data,required_columns)

            
        else:
            print(f"No keyword match found in file: {file_name}")
    else:
        print(f"File {file_name} does not match criteria.")
