import configparser
import csv
import glob
import json
import os
import random
import re
import sys
import time
from tkinter import filedialog

import pandas as pd
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# ブラウザ操作用 webdriver、ポジ、ネガを引数に取ってgenerate


def gen_Image(driver, prompt, negative, gen_width, gen_height):
    """
    おい、こっちの関数はブラウザを操って、指定されたプロンプトで画像を生成するんだぜ。
    Stable Diffusionってやつを使ってるんだ。
    ポジティブプロンプト、ネガティブプロンプト、幅と高さを指定して、画像生成の魔法をかけるんだ。

    Args:
        driver (WebDriver): SeleniumのWebDriverだ。ブラウザをグルグル動かすために使うんだ。
        prompt (str): 画像生成の呪文みたいなもんだな。ポジティブプロンプトだ。
        negative (str): これも画像生成の呪文。ネガティブプロンプトってやつだ。
        gen_width (int): 生成する画像の幅。0だと変更なし。
        gen_height (int): 生成する画像の高さ。こっちも0だと変更なし。

    Returns:
        bool: 画像生成の呪文がうまくいったらTrue、何かミスったりビジーだったらFalseを返すぜ。
    """
    # タイトルが"Stable Diffusion"でない場合は準備ミスかビジーなのでFalseを返してやり直させる
    titlechk = driver.title

    if titlechk != "Stable Diffusion":
        return False
    print("title OK")

    actions = ActionChains(driver)

    # ポジティブプロンプト
    element_posi = driver.find_element(
        By.XPATH, '//*[@id="txt2img_prompt"]/label/textarea')
    driver.execute_script(f'arguments[0].value = "{prompt}"', element_posi)
    # 力技で変更を認識させる（末尾にスペースを入力）
    driver.execute_script("arguments[0].focus()", element_posi)
    actions.send_keys(Keys.SPACE).perform()

    # ネガティブプロンプト
    element_nega = driver.find_element(
        By.XPATH, '//*[@id="txt2img_neg_prompt"]/label/textarea')
    driver.execute_script(f'arguments[0].value = "{negative}"', element_nega)
    # 力技で変更を認識させる（末尾にスペースを入力）
    driver.execute_script("arguments[0].focus()", element_nega)
    actions.send_keys(Keys.SPACE).perform()

    if gen_width != 0:
        element_width = driver.find_element(
            By.XPATH, '//*[@id="txt2img_width"]/div[2]/div/input')
        driver.execute_script(
            f"arguments[0].value = '{gen_width}'", element_width)
        # 力技で変更を認識させる（↑↓とキーを押す）
        driver.execute_script("arguments[0].focus()", element_width)
        actions.send_keys(Keys.UP).perform()
        actions.send_keys(Keys.DOWN).perform()

        element_height = driver.find_element(
            By.XPATH, '//*[@id="txt2img_height"]/div[2]/div/input')
        driver.execute_script(
            f"arguments[0].value = '{gen_height}'", element_height)
        # 力技で変更を認識させる（↑↓とキーを押す）
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
    while driver.title == titlechk:
        time.sleep(0.02)
        if i % 5 == 0:
            print("|", end="")
        i = i + 1
        if i > 500:
            print("10秒待っても生成開始を確認できませんでした。スキップします。")
            return True
    # タイトルが [〇% ETA:〇s] に変化した。元に戻るまで待つ
    i = 1
    while driver.title != titlechk:
        time.sleep(0.02)
        if i % 5 == 0:
            print("|", end="")
        i = i + 1
        if i > 1000:
            print("生成完了を検知できず10秒以上待っています。次の処理を始めます。")
            break

    return True


def get_df(csvname, dataframe, key, value, column):
    """
    おい、CSVからデータを掘り出したいときはこの関数を使うんだぜ。
    指定したキーと値でDataFrameを探し回って、欲しい列の情報をピンポイントで抜き出すマジックだ。

    例えば、「何もしない」というダラけたコマンドの時のリアクションが気になるなら、
    コマンド名が「何もしない」の行を見つけ出して、そこからプロンプト列の値を掴むんだ。
    もし該当するデータがなければ空文字を、なにかおかしなことが起きたら 'Error' って返してやるから安心しろ。

    Args:
        csvname (str): 調べたいCSVの名前。どんなデータでも引っ張ってこれるぜ。
        dataframe (DataFrame): こいつが宝の地図。Pandas DataFrameでね。
        key (str): 探し出すべき情報が載っている列名だ。これがあるおかげで迷わずに済む。
        value (str): お目当ての値。これに一致する行を探すんだ。
        column (str): ここに書いてある列から値を持ってくる。

    Returns:
        str: 探し出した宝物…って言うか、対象の値だな。もし見つからない場合は 'Error' さ。

    Examples:
        こう使うんだ：get_df(csvname, dataframe, "コマンド名", "何もしない", "プロンプト")
        上の例で言えば、「何もしない」という行の「プロンプト」列の値をずばり返してくれる。
    """
    try:
        result = dataframe.loc[dataframe[key] ==
                            value, column].fillna("").values[0]
    except KeyError as e:
        print(f"Error: {csvname}: 指定したキー '{key}' または列 '{column}' が見つかりません。{e}")
    except IndexError as e:
        print(f"Error: {csvname}: 指定したインデックスが範囲外。{e}")
    # pandas特有のエラーも追加する、例えばDataErrorなど
    except pd.errors.DataError as e:
        print(f"Error: {csvname}: データ処理に関するエラー。{e}")
    except Exception as e:
        # 不明な他のエラーは個別に対応が必要かもしれない
        print(f"不明な他のエラー: {e}")
        return "Error"
    return result


def get_df_2key(csvname, dataframe, key, value, subkey, subvalue, column):
    """
    指定されたCSVから、2つの検索キーとそれに対応する値を元にデータを探査し、
    条件を満たす行から特定の列の値を引っ張り出してくる関数だぜ。

    この関数は `key = value` かつ `subkey = subvalue` の条件に合った行を見つけ、
    さらに `column` で指定された列の値を取得するぜ。まさに2段階の鍵を使った宝探しのようなものだ。

    Args:
        csvname (str): CSVファイルの名前。掘り出すデータの宝の地図のようなものさ。
        dataframe (DataFrame): 検索対象のPandas DataFrameオブジェクト。
        key (str): 1つ目のキーとなる列名。
        value (str): `key`列における検索する値。
        subkey (str): 2つ目のキーとなる列名。
        subvalue (str): `subkey`列における検索する値。
        column (str): 最终的に値を取得したい列の名称だ。

    Returns:
        str: 検索条件を満たす値。もし該当なしなら空文字、おかしなことが起きたら 'Error' を返す。

    """
    try:
        # keyとsubkeyの両方で条件を満たす行を検索し、column列の値を取得
        result = dataframe.loc[
            (dataframe[key] == value) & (dataframe[subkey] == subvalue),
            column
        ].fillna("").values[0]
    except KeyError as e:
        print(
            f"Error: キー '{key}'、'{subkey}'、または列 '{column}' が {csvname} に存在しません - {e}")
    except IndexError as e:
        print(
            f"Error: 条件を満たす行 {key} = {value} かつ {subkey} = {subvalue} が {csvname} に見つかりませんでした - {e}")
    except Exception as e:
        # ここでは最終手段として一般的な例外を捕捉しますが、できればエラーコードを絞るべきです
        print(f"エラー: {csvname}の処理中に予期せぬ例外が発生しました - {e}")
        return "Error"

    # 成功した場合は結果を返す
    return result


def chikan(text, csvfile_path):
    """置換機能
    文字列中に%で囲まれた部分があればreplacelist.csvに基づいて置換する機能

    Args:
        text (_type_): _description_
        csvfile_path (_type_): csvのパス CSVMのせいで不要な引数のやり取りが発生 あとで直す

    Returns:
        _type_: _description_
    """
    csvname, csvfile_path = csvm.find_csv_path('replacelist.csv')
    csv_chi = pd.read_csv(filepath_or_buffer=csvfile_path)
    # 正規表現で置換対象("%"で挟まれた文字列)をリスト化
    置換対象 = re.findall('%.*?%', text)
    if len(置換対象) > 0:
        # 見つかった置換対象リストの数だけ繰り返し
        for chi in 置換対象:
            # %抜きの文字列でcsvを検索する
            csv参照用 = chi.strip("%")
            text = re.sub(chi, get_df(csvname, csv_chi,
                                    "置換前", csv参照用, "置換後"), text)
            # get_dfがエラーを出した場合、文字列"Error"に置換される
    return text


# GUI
class ReadConfig:
    """
    このクラスは、設定ファイル（config.ini）を扱うためのものだぜ。
    ファイルを読み込んで、ユーザーが選んだフォルダパスを保存するんだ。使い方は簡単、
    インスタンスを作ってフォルダ選択を促すだけ。あとは、このクラスが裏で全てやってくれるぜ。

    主な機能:
    - INIファイルの読み込み: コンストラクタでconfig.iniを読み込む。
    - フォルダ選択ダイアログの表示: ユーザーがフォルダを選ぶと、そのパスをconfig.iniに書き込む。

    使い方:
    1. クラスのインスタンスを作成。
    2. select_folderメソッドを呼び出して、フォルダ選択ダイアログを表示。
    3. ユーザーがフォルダを選ぶと、そのパスがconfig.iniに保存されるぜ。

    シンプルだけど、めちゃくちゃ便利なクラスだぜ！
    """

    def __init__(self):
        # iniファイル読み込み
        self.config = configparser.ConfigParser()
        self.config.read("./config.ini")
        self.selecteddir = None

    def select_folder(self):
        """
        # フォルダ選択ダイアログ表示(テキスト監視フォルダ)
        ユーザーにフォルダを選択させるダイアログを表示し、選択されたフォルダのパスを返します。
        選択されたフォルダパスはINIファイルにも保存されます。

        ダイアログを使ってフォルダが選択されると、そのパスがクラスのインスタンス変数に
        設定されるほか、設定ファイルにも記録されるんだ。これを使えば、ユーザーの選んだフォルダの
        パスを取得して、あとで使いたい時に手間なく引っ張り出せるぜ。

        Returns:
            str: ユーザーによって選択されたフォルダの絶対パス。
                ユーザーがキャンセルや選択なしでダイアログを閉じた場合は、空文字列が返される。
        """
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.selecteddir = folder_path
            print(f"Selected folder: {self.selecteddir}")
            # iniに記入
            self.config.set("Paths", "Path1", self.selecteddir)
            with open("config.ini", "w", encoding="utf-8") as configfile:
                self.config.write(configfile)
            return self.selecteddir

# 解像度文字列の取得関数はバリアントごとのcsvを読むのでバリアント個別ファイルに移動
# ちょっと違和感あるので戻すかも

# 解像度文字列を解釈する関数


def get_width_and_height(kaizoudo, replacelist):
    """
    渡された解像度文字列を解釈し、幅と高さの整数値のペアを返します。

    書式は "幅x高さ" で、複数のオプションがある場合はカンマで区切ります。
    また、置換リストを適用し "%文字列%" を特定の値に置換することができます。

    例えば、"512x768,768x512,1024x512" と書かれている場合は、ランダムに一つを選んで
    その解像度を適用します。置換機能も組み込まれているから、柔軟な指定が可能だ。

    Args:
        kaizoudo (str): 解読する解像度を示す文字列です。
        replacelist (dict): 置換処理のためのリスト（辞書型）です。

    Returns:
        tuple: (幅, 高さ) の形で解像度の数値を返します。
            解読できない場合やエラーがある場合は (0, 0) を返します。

    Raises:
        ValueError: 解像度文字列が不正であるか、数値に変換できない値が含まれている場合。
    """
    # 解像度欄でも置換機能を使えるようにする。%で囲まれた文字列があると置換を試みる。
    kaizoudo = chikan(kaizoudo, replacelist)

    # 読み出した結果が空欄やエラーの場合は0,0を返す。解像度の変更はスキップされる。
    if kaizoudo in ("", "Error"):
        print("解像度指定なし")
        return 0, 0
    print("解像度変更あり")

    # ","で分割されている場合、ランダムで選ぶ
    # 例 3択ランダムなら"512x768,768x512,1024x512"みたいに書く。置換機能を使ってもよい。
    if "," in kaizoudo:
        splitkai = re.split(",", kaizoudo)
        ra = random.randrange(len(splitkai))
        kaizoudo = splitkai[ra]

    # xで分割 (区切り文字としてXと*と×も認める)
    kai = re.split("[xX*×]", kaizoudo)
    # エラー処理2 splitで2要素に分割されなかった場合
    if len(kai) != 2:
        print("解像度取得に失敗。splitで2要素に分割されなかった。解像度変更を中止")
        return 0, 0

    try:
        width = int(kai[0])
        height = int(kai[1])
    except Exception as e:
        # エラー処理3 splitできたが数値として認識できない場合
        print(f"解像度取得に失敗。splitできたが数値として認識できなかった。詳細:{e}")
        print("解像度変更を中止")
        return 0, 0

    return width, height


class CSVManager:
    """
    このクラスはCSVファイルとのやり取りをスムーズにしてくれるマジックアイテムだ。
    CSVファイルからのデータ読み込みや、それをキャッシュする仕組み、さらには新しいCSVへの書き込みまで、
    こいつがあれば一通りの操作をバッチリこなせるぜ。

    CSVファイルリストを生成して、特定のバリアントの全CSVファイルをキャッチ。
    読み込んだものはキャッシュに保存しておき、再利用が可能になっているんだ。
    チームでの作業や大量のデータを扱いたい時にも、この便利さは必見。

    Attributes:
        csvlist (str): CSVファイルパスのリストが記載されたCSVファイルへのパス。
        loaded_csvs (dict): 読み込み済みのCSVデータをキャッシュするための辞書。
    """

    def __init__(self):
        self.csvlist = self.generate_csvlist()
        self.loaded_csvs = {}  # キャッシュ用

    def generate_csvlist(self):
        """
        現在のバリアントのCSVファイルリストを生成し、ファイルとして保存するんだ。
        おまえが 'era2webui.py' からインポートしてるバリアントに基づいて、
        対象ディレクトリ内のCSVファイルのパスをリストアップしてくれるぜ。

        そうして得られたCSVファイルリストは、操作がしやすいように
        'csv_list.csv' ファイルに名前とパスが記録される。
        バリアント選択が済んでない場合は教えてやるからな。

        Returns:
            str: 作成したCSVファイルリストのパス。バリアント選択が未完了の場合はNoneを返す。
        """
        # sub.pyが存在するディレクトリのパスを取得
        base_dir = os.path.dirname(__file__)

        # era2webui.pyのパスを構築
        era2webui_path = os.path.join(base_dir, 'era2webui.py')

        # era2webui.pyを読み込んでインポート文を検索
        with open(era2webui_path, 'r', encoding='utf-8') as file:
            content = file.read()

        # コメントアウトされていないインポート文を検索
        match = re.search(
            r'^from (eratohoYM|eraTW|eraImascgpro)', content, re.MULTILINE)

        if match:
            # 一致したモジュール名を取得
            imported_module = match.group(1)
            print(f"対応するeraバリアント: {imported_module}")

            # モジュール名を含むディレクトリへのパスを組み立てる
            variantdir = os.path.join(
                os.path.dirname(__file__), imported_module)
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

    def read_csv(self, csv_name):
        """
        指定されたCSVファイル名にマッチするファイルを探し出し、その中身を読み込む。

        CSVファイルの名前から実際のファイルパスを探し出して、データをPandasの
        DataFrameに読み込むんだ。ファイルがちゃんとそこにあるかはこのメソッドが
        確かめてくれるから、万が一見当たらなければおまえに教えるぜ。

        Args:
            csv_name (str): 読み込みたいCSVファイルの名前。
            
        Returns:
            DataFrame/None: CSVデータを含むPandasのDataFrame、
                            またはCSVファイルが見つからない場合はNone。
        """
        csv_path = self.find_csv_path(csv_name)
        if csv_path is None:
            print(f"{csv_name} のPathが見つからないぜ")
            return None
        return self.load_csv(csv_path)

    # csvlistup関数でリストアップしたcsvlistをファイル名をキーに検索Pathを返す
    def find_csv_path(self, csv_name):
        """
        CSVファイル名から正しい道すじを探し当て、その貴重なパス情報を手に入れる。

        おまえが欲しいCSVの名前を小さな声で教えてくれたら、こいつがお前の行く先を
        案内してくれるからな。csvlistを拾い読みして、指定されたファイル名と同じ名前の
        ラインを見つけ出す。そしたら、我々にとって重要なパス情報をすぐにでも
        提供してくれるんだ。

        Args:
            csv_name (str): おまえが見つけたいCSVファイルの名前だ。

        Returns:
            tuple: おまえの求めるファイルが実際にどこに落ちてるのか、その名前とパスをタプルで提供する。
                行が見つからなかった場合、悲しいけど None を返すことになるぞ。
        """
        # CSVファイルリストを読み込む
        with open(self.csvlist, mode='r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if row[0].lower() == csv_name.lower():  # 大文字小文字を区別しない比較
                    return row[0], row[1]  # 名前とパスを返す｡ 名前はエラー表示用
        print(f"{csv_name}のPathが見つからないぜ")  # ファイルが見つからない場合
        return None

    def load_csv(self, path_tuple):
        """
        CSVファイルの真髄を解き放つための儀式だ。この関数を使ってデータを召喚するんだ。

        path_tuple が指し示す場所にあるCSVファイルから内容を読み上げて、
        それをPandasが喰らいつくような、データフレームの形で吐き出す。
        最初の行が数字から始まってると、ヘッダーが無いってことで、適当に作ってやるから安心しろよ。

        Args:
            path_tuple (tuple): ('ファイル名', 'ファイルパス') の形のタプル。渡されたパスでCSVを読むぞ。

        Returns:
            List[dict]: CSVの全ての行が辞書型に変換されたリストだ。
                        ヘッダーがなければ適当に作って、列を辞書のキーとする。
        """
        csv_path = path_tuple[1]  # pathだけ取り出す
        with open(csv_path, mode='r', encoding='utf-8-sig') as file:
            # 最初の行だけを読み込む
            first_line = file.readline()

            # ファイルを先頭に戻す
            file.seek(0)

            # 最初の行が数字で始まる場合はヘッダを追加してkeyに使う
            if first_line[0].isdigit():
                # ここでヘッダを定義する必要がある
                headers = [f'column{i}' for i in range(
                    len(first_line.split(',')))]
                reader = csv.DictReader(file, fieldnames=headers)
            # 文字で始まる場合はcsv.DictReaderを使用
            else:
                reader = csv.DictReader(file)

            data = [dict(row) for row in reader]
        # 戻り値は辞書のリスト
        return data

    # DictをCSVに出力する
    def write_dict_to_csv(self, file_name, data_dict, headers=None, is_nested_dict=True):
        """
        辞書を渡すと、その内容をCSVファイルに転写してくれる便利な機能だ。
        おれたちが蓄えてきたデータの宝庫を、世の中に分かち合うためには欠かせない手順さ。
        
        ネストされた辞書かどうかを指定することもできるし、ヘッダーを自分で設定したいときは
        それもできるぜ。キーと値のペアを、ずらりと並んだCSVファイルにするんだ。

        Args:
            file_name (str): 書き込みたいCSVファイルの名前だ。
            data_dict (dict): CSVに変換される辞書。ネストしてもいいし、シンプルなものでもOK。
            headers (list[str], optional): CSVのヘッダーを明示的に指定する場合に使う。指定がなければ辞書から自動生成される。
            is_nested_dict (bool, optional): 渡される辞書がネストされた構造かどうか。デフォルトはTrue。

        Returns:
            None: ファイルに書き込みを完了したら、特に何も返さない。
        """
        with open(file_name, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            if headers:
                writer.writerow(headers)
            else:
                # ネストされた辞書の場合、最初の要素からヘッダーを取得する
                if is_nested_dict and data_dict:
                    headers = ['Key'] + \
                        list(data_dict[next(iter(data_dict))].keys())
                    writer.writerow(headers)

            for key, value in data_dict.items():
                if is_nested_dict:
                    # ネストされた辞書の場合、値からリストを作成する
                    row = [key] + [value.get(header) for header in headers[1:]]
                else:
                    # ネストされていない辞書（キーと単一の値）の場合
                    row = [key, value]
                writer.writerow(row)


class SaveJSONHandler:
    """
    saveのjsonを扱いやすい形にするクラス
    """

    def __init__(self, savetxt_path):
        self.data = None
        self.load_save(savetxt_path)
        self.process_json()
        self.cast_data()

    def load_save(self, savetxt_path):
        """渡されたpathからJSONを読んで辞書に格納
        Args:
            new_savetxt_path (str): txtのpath 
            FileHandlerとの兼ね合いは後で調整
        """
        if savetxt_path is None:
            print("エラー: ファイルパスが指定されていません。txtの更新を待っています。")
            return  # メソッドをここで終了させる
        try:
            with open(savetxt_path, 'r', encoding='utf-8-sig') as file:
                self.data = json.load(file)
        except FileNotFoundError as e:
            print(f'エラー: ファイル "{savetxt_path}" が見つかりません。 - {str(e)}')
        except json.JSONDecodeError as e:
            print(
                f'エラー: ファイル "{savetxt_path}" の出力がjsonフォーマットになってない。 - {str(e)}')
            sys.exit()

    def process_json(self):
        """
        self.dataの処理部を引き渡すだけ
        こっちのほうがいいよってAI魔理沙が言うから
        よくわかりません
        """
        self._process_nested_data(self.data)

    def _process_nested_data(self, data=None, parent_key=''):
        """
        ネストされたJSONデータ構造を再帰的に処理する。
        このメソッドは、与えられたJSONデータ（辞書またはリスト）の各要素を走査し、
        必要な処理（例：データの変換）を行う。

        Args:
            data (dict or list, optional): 処理するJSONデータ。辞書またはリスト形式を想定。
                Noneが指定された場合、クラスのdata属性を使用する。デフォルトはNone。
            parent_key (str, optional): 現在処理中のデータの親キーのパス。
                ネストされたデータ構造内での現在の位置を表す。デフォルトは空文字列 ('')。
        """
        if data is None:
            data = self.data

        if isinstance(data, dict):
            for key, value in data.items():
                new_key = f"{parent_key}.{key}" if parent_key else key
                self._process_nested_data(value, new_key)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                new_key = f"{parent_key}[{i}]"
                self._process_nested_data(item, new_key)

        else:
            # ここで値を処理する。例えば表示するのはデバッグ用
            print(
                f"Key: {parent_key} - Value: {data} (Type: {type(data).__name__})")

    def cast_data(self, data=None):
        """
        データ構造の中を進んで、必要に応じて型変換を施すぜ。
        辞書やリストが渡されたら、その中身も掘り下げて、文字列が数字だけを
        含んでいたら整数に、そうじゃなければそのままにしておくんだ。

        Args:
            data (Any, optional): 型変換を施したいデータ。何も渡されなかったら、
                                インスタンス変数 self.data が使われる。デフォルトはNone。

        Returns:
            Any: 型変換後のデータ。辞書やリスト内の要素も適宜変換される。
        """
        if data is None:
            data = self.data  # 初回呼び出しではself.dataを使用

        if isinstance(data, dict):
            for key, value in data.items():
                data[key] = self.cast_data(value)  # 再帰的に型変換

        elif isinstance(data, list):
            return [self.cast_data(item) for item in data]  # リストも再帰的に型変換

        elif isinstance(data, str) and data.isdigit():
            return int(data)  # 文字列が数字のみなら整数に変換

        return data

    def get_save(self, key):
        """
        お前が渡したキーにピタッと合うデータを、JSONの海から引き上げてくる機能だ。

        JSONファイルはもう読み込んである...といいんだが、もしそれがまだなら
        お前にエラーメッセージを叩きつける。そしたら、適当なファイルを読み込むんだな。
        この関数が呼ばれたら、指定したキーでデータを探してその値を返す。
        もしキーが見当たらなかったらしゃーなし、Noneを返すぞ。

        Args:
            key (str): 辞書型で読み込んだJSONデータから取得したい値のキーだ。

        Returns:
            Any: キーに対応する値、もしくはキーが存在しない場合はNone。
        """
        if not self.data:
            print('エラー: JSONファイルが読み込まれていません。')
            return None  # デフォルト値をNoneにして明示的に問題を示す
        # 辞書から値を取得してそのまま返す
        return self.data.get(key)


csvm = CSVManager()
