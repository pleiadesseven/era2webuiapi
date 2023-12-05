from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import time
import os
import random
import pandas as pd
import re
import tkinter as tk
from tkinter import filedialog
import configparser
from selenium.webdriver.common.by import By
import glob
import csv
from modulefinder import ModuleFinder
from pathlib import Path
import re
import csv


# ブラウザ操作用 webdriver、ポジ、ネガを引数に取ってgenerate
def gen_Image(driver,prompt,negative,gen_width,gen_height):

    # タイトルが"Stable Diffusion"でない場合は準備ミスかビジーなのでFalseを返してやり直させる
    titlechk=driver.title

    if titlechk != "Stable Diffusion":
        return False
    
    print("title OK")

    actions = ActionChains(driver)

    # ポジティブプロンプト
    element_posi = driver.find_element(By.XPATH,'//*[@id="txt2img_prompt"]/label/textarea')
    driver.execute_script(f'arguments[0].value = "{prompt}"', element_posi)
    #力技で変更を認識させる（末尾にスペースを入力）
    driver.execute_script("arguments[0].focus()", element_posi)
    actions.send_keys(Keys.SPACE).perform()

    # ネガティブプロンプト
    element_nega = driver.find_element(By.XPATH,'//*[@id="txt2img_neg_prompt"]/label/textarea')
    driver.execute_script(f'arguments[0].value = "{negative}"', element_nega)
    #力技で変更を認識させる（末尾にスペースを入力）
    driver.execute_script("arguments[0].focus()", element_nega)
    actions.send_keys(Keys.SPACE).perform()


    if gen_width != 0:
        element_width = driver.find_element(By.XPATH,'//*[@id="txt2img_width"]/div[2]/div/input')
        driver.execute_script(f"arguments[0].value = '{gen_width}'", element_width)
        #力技で変更を認識させる（↑↓とキーを押す）
        driver.execute_script("arguments[0].focus()", element_width)
        actions.send_keys(Keys.UP).perform()
        actions.send_keys(Keys.DOWN).perform()

        element_height = driver.find_element(By.XPATH,'//*[@id="txt2img_height"]/div[2]/div/input')
        driver.execute_script(f"arguments[0].value = '{gen_height}'", element_height)
        #力技で変更を認識させる（↑↓とキーを押す）
        driver.execute_script("arguments[0].focus()", element_height)
        actions.send_keys(Keys.UP).perform()
        actions.send_keys(Keys.DOWN).perform()


    # Ctrl+EnterでGenerateする
    actions.key_down(Keys.CONTROL)
    actions.key_down(Keys.ENTER)
    actions.perform()

    # -----生成が行われたかの判定。とりあえずブラウザのtitleで判断。（生成中はタイトルが変わる。"Stable Diffusion"に戻ったら完了）タイトル変化に1秒ほどのラグがあり、1秒未満で完了すると検知できない

    print("生成中", end="")
    i = 1
    while (driver.title == titlechk):
        time.sleep(0.02)
        if i % 5 == 0:
            print("|", end="")
        i = i + 1
        if i > 500:
            print("10秒待っても生成開始を確認できませんでした。スキップします。")
            return True
    # タイトルが [〇% ETA:〇s] に変化した。元に戻るまで待つ
    i = 1
    while (driver.title != titlechk):
        time.sleep(0.02)
        if i % 5 == 0:
            print("|", end="")
        i = i + 1
        if i > 1000:
            print("生成完了を検知できず10秒以上待っています。次の処理を始めます。")
            break

    return True


# csv読み出し用
# key = value になる行を探して　列名 column の要素を取得する
# 例 : get_df(csv_tra,"コマンド名","何もしない","プロンプト") で何もしない時のプロンプトを返す
# csvの該当箇所が空欄の時は""を返す
# 検索条件がおかしい場合は"Error"を返す
def get_df(csvname, dataframe, key, value, column):
    try:
        result = dataframe.loc[dataframe[key] == value, column].fillna("").values[0]
    except Exception as e:
        print("Error: {}".format(e))
        print("取り出そうとした要素:{}内の{}={}なる行の{}".format(csvname,key,value,column))
        return "Error"
    return result

# csv読み出し用 検索条件が2列で構成される場合
def get_df_2key(csvname, dataframe, key, value, subkey, subvalue, column):
    try:
        result = dataframe.loc[(dataframe[key] == value) & (dataframe[subkey] == subvalue), column].fillna("").values[0]
    except Exception as e:
        print("Error: {}".format(e))
        print("取り出そうとした要素: {}内の{}={}かつ{}={}なる行の{}".format(csvname,key,value,subkey,subvalue,column))
        return "Error"
    return result

# 置換機能
# 文字列中に%で囲まれた部分があればReplaceList.csvに基づいて置換する機能
def chikan(text,csvfile_path):
    csv_chi = pd.read_csv(filepath_or_buffer=csvfile_path)
    # 正規表現で置換対象("%"で挟まれた文字列)をリスト化
    置換対象 =re.findall('%.*?%',text)
    if len(置換対象) > 0:
        # 見つかった置換対象リストの数だけ繰り返し
        for chi in 置換対象:
            # %抜きの文字列でcsvを検索する
            csv参照用 = chi.strip("%")
            text = re.sub(chi,get_df(csv_chi,"置換前",csv参照用,"置換後"),text)
            # get_dfがエラーを出した場合、文字列"Error"に置換される
    return text


# GUI
class readconfig:
    def __init__(self):
        # iniファイル読み込み
        self.config = configparser.ConfigParser()
        self.config.read("./config.ini")

    # フォルダ選択ダイアログ表示(テキスト監視フォルダ)
    def select_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.selectedDir = folder_path
            print(f"Selected folder: {self.selectedDir}")
            # iniに記入
            self.config.set("Paths", "Path1", self.selectedDir)
            with open("config.ini", "w") as configfile:
                self.config.write(configfile)
            return self.selectedDir


# 解像度文字列の取得関数はバリアントごとのcsvを読むのでバリアント個別ファイルに移動
# ちょっと違和感あるので戻すかも

# 解像度文字列を解釈する関数
def get_width_and_height(kaizoudo,Replacelist):

    # 解像度欄でも置換機能を使えるようにする。%で囲まれた文字列があると置換を試みる。
    kaizoudo = chikan(kaizoudo,Replacelist)

    # 読み出した結果が空欄やエラーの場合は0,0を返す。解像度の変更はスキップされる。
    if kaizoudo in ("","Error"):
        print("解像度指定なし")
        return 0,0
    print("解像度変更あり")

    # ","で分割されている場合、ランダムで選ぶ
    # 例 3択ランダムなら"512x768,768x512,1024x512"みたいに書く。置換機能を使ってもよい。
    if "," in kaizoudo:
        splitkai = re.split(",",kaizoudo)
        ra = random.randrange(len(splitkai))
        kaizoudo = splitkai[ra]

    # xで分割 (区切り文字としてXと*と×も認める)
    kai = re.split("[xX*×]",kaizoudo)
    # エラー処理2 splitで2要素に分割されなかった場合
    if len(kai) != 2:
        print("解像度取得に失敗。splitで2要素に分割されなかった。解像度変更を中止")
        return 0,0

    try:
        width = int(kai[0])
        height = int(kai[1])
    except Exception as e:
        # エラー処理3 splitできたが数値として認識できない場合
        print(f"解像度取得に失敗。splitできたが数値として認識できなかった。詳細:{e}")
        print("解像度変更を中止")
        return 0,0
    
    return width,height


def generate_csvlist():
    # sub.pyが存在するディレクトリのパスを取得
    base_dir = os.path.dirname(__file__)

    # era2webui.pyのパスを構築
    era2webui_path = os.path.join(base_dir, 'era2webui.py')

    # era2webui.pyを読み込んでインポート文を検索
    with open(era2webui_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # コメントアウトされていないインポート文を検索
    match = re.search(r'^from (eratohoYM|eraTW|eraImascgpro)', content, re.MULTILINE)

    if match:
        # 一致したモジュール名を取得
        imported_module = match.group(1)
        print(f"対応するeraバリアント: {imported_module}")

        # モジュール名を含むディレクトリへのパスを組み立てる
        variantdir = os.path.join(os.path.dirname(__file__), imported_module)
        csvdir = os.path.join(variantdir, 'csvfiles')

        # 指定ディレクトリ内の全てのCSVファイルのパスを取得
        csv_files = glob.glob(os.path.join(csvdir, '*.csv'))

        # CSVファイルの名前とアドレスをCSVファイルに保存
        csv_list_path = os.path.join(variantdir, 'csv_list.csv')
        with open(csv_list_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["name", "path"])
            for file in csv_files:
                file_name = os.path.basename(file)
                writer.writerow([file_name, file])

        print(f"{imported_module}のCSVファイルのリストを '{csv_list_path}' に保存したぜ。")
        return csv_list_path
    else:
        print("バリアントを選んでfromのコメントアウトを解除してください")
        return None

# グローバル変数としてcsvlistを定義
csvlist = generate_csvlist()


#csvlistup関数でリストアップしたcsvlistをファイル名をキーに検索Pathを返す
def find_csv_path(csv_name):
    # CSVファイルリストを読み込む
    with open(csvlist, mode='r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if row[0].lower() == csv_name.lower():  # 大文字小文字を区別しない比較
                return row[1]  #パスを返す
    return print (f"{csv_name}のPathが見つからないぜ") # ファイルが見つからない場合


def load_csv(csv_path):
    with open(csv_path, mode='r', encoding='utf-8') as file:
        # 最初の行だけを読み込む
        first_line = file.readline()

        # ファイルを先頭に戻す
        file.seek(0)

        # 最初の行が数字で始まる場合はcsv.readerを使用
        if first_line[0].isdigit():
            reader = csv.reader(file)
            data = [row for row in reader]
        # 文字で始まる場合はcsv.DictReaderを使用
        else:
            reader = csv.DictReader(file)
            data = [row for row in reader]
    #戻り値はリスト型
    return data
