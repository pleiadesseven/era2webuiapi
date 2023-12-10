import csv
import glob
import os
import re
import pandas as pd



def search_imported_variant():
    """ここがなんか汚いが今のところここでしか使わない
    'era2webui.py' からインポートされているバリアントを検索する。
    Returns:
        str: インポートされているバリアントの名前。見つからない場合はNoneを返す。
    """
    # カレントディレクトリのパスを取得
    base_dir = os.path.dirname(__file__)
    # カレントディレクトリの親ディレクトリのパスを取得
    parent_dir = os.path.dirname(base_dir)
    # 親ディレクトリにある 'era2webui.py' へのパスを作成
    era2webui_path = os.path.join(parent_dir, 'era2webui.py')

    try:
        with open(era2webui_path, 'r', encoding='utf-8') as file:
            content = file.read()
        match = re.search(
            r'^from (eratohoYM|eraTW|eraImascgpro)', content, re.MULTILINE)
        if match:
            return match.group(1)
        else:
            print("バリアントを選んでfromのコメントアウトを解除してください")
            return None
    except FileNotFoundError:
        print(f"'{era2webui_path}' が見つかりません。")
        return None



class CSVMFactory:
    """
    複数箇所から呼び出されるのでファクトリークラスとかでインスタンスを実行させて
    CSVMの多重起動を防ぐ
    Returns:
        _type_: _description_
    """
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = CSVManager()
        return cls._instance
    

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
        self.csvlist = {}
        self.csvdatas = {}
        self.generate_csvlist()
        self.csvdata_import()
        self.combine_character_csvs() #Add_Characterを結合してCharacter.csvとして扱うので必ずself.csvdata_import()の後に呼べ


    def generate_csvlist(self):
        """
        現在のバリアントのCSVファイルリストを生成し、クラス変数保存するんだ。
        'era2webui.py' からインポートしてるバリアントに基づいて、
        対象ディレクトリ内のCSVファイルのパスをリストアップしてくれるぜ。

        そうして得られたCSVファイルリストは、操作がしやすいように
        'csv_list.csv' ファイルに名前とパスが記録される。
        バリアント選択が済んでない場合は教えてやるからな。
        """
        # 一致したモジュール名を取得
        imported_module = search_imported_variant()
        print(f"対応するeraバリアント: {imported_module}")

        if imported_module:
            # モジュールのあるディレクトリの親ディレクトリを取得
            base_dir = os.path.dirname(os.path.dirname(__file__))
            # モジュール名を含むディレクトリへのパスを組み立てる
            variantdir = os.path.join(base_dir, imported_module)
            csvdir = os.path.join(variantdir, 'csvfiles')

            # 指定ディレクトリ内の全てのCSVファイルのパスを取得し、辞書に格納
            self.csvlist = {os.path.basename(file): file for file in glob.glob(
                os.path.join(csvdir, '*.csv'))}

            print(f"{imported_module}のCSVファイルのリストをCSVManagerクラス変数に格納したぜ。")
        else:
            print("バリアントが見つからないか、選択されていないようだ。")


    def csvdata_import(self):
        # ここでcsvlist内のCSVファイルを読み込んでいる
        for csv_name, _ in self.csvlist.items():
            df = self.read_csv(csv_name)
            if df is not None:
                # クラス辞書にDataFrame形式でデータを格納
                self.csvdatas[csv_name] = df


    def combine_character_csvs(self):
        """
        'Character.csv' と 'Add_Character.csv' を結合し、
        結合されたDataFrameを 'Character.csv' キーで保存する。
        """
        # パスの名前に基づいて両方のCSVファイルをDataFrameとして読み込む
        char_df = self.read_csv('Character.csv')
        add_char_df = self.read_csv('Add_Character.csv')

        # もしファイルが見つかれば、DataFrame同士を結合する
        if char_df is not None and add_char_df is not None:
            combined_df = pd.concat([char_df, add_char_df]).reset_index(drop=True)

            # 統合したDataFrameを 'Character.csv' キーでcsvdatasに格納
            self.csvdatas['Character.csv'] = combined_df


    def read_csv(self, csv_name):
        """
        CSVファイル名からPandas DataFrameを読み込んで返す。

        Args:
            csv_name (str): 読み込むCSVファイルの名前。

        Returns:
            DataFrame: CSVから読み込んだデータを含むPandasのDataFrame、
                        またはCSVファイルが見つからない場合はNone。
        """
        # find_csv_path メソッドを使ってファイルの正しいパスを取得する例
        _, file_path = self.find_csv_path(csv_name)
        if file_path is None:
            print(f"read_csv:ファイル名 {csv_name} に対応するパスが見つからなかったぜ。")
            return None

        try:
            df = pd.read_csv(file_path)
            return df
        except FileNotFoundError:
            print(f"read_csv:ファイル {file_path} が見つからなかったぜ。")
            return None


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
        for name, path in self.csvlist.items():
            if name.lower() == csv_name.lower():  # 大文字小文字を区別しない比較
                return name, path  # 名前とパスを返す｡ 名前はエラー表示用
        print(f"find_csv_path:'{csv_name}' という名前のCSVファイルは見つからなかったぜ。")
        return None, None


    def process_csv_data(self, csv_name):
        """
        CSVファイルのデータを読み込んでPandas DataFrameに変換し、
        それを辞書形式にする。

        Args:
            csv_name (str): 読み込むべきCSVファイルの名前。

        Returns:
            dict: CSVデータを辞書形式に変換したもの。
        """
        # find_csv_path メソッドを使ってファイルのパスを取得する想定
        _, file_path = self.find_csv_path(csv_name)
        if file_path is None:
            print(f"{csv_name} のPathが見つからないぜ")
            return None
        
        try:
            df = pd.read_csv(file_path)
            return df.to_dict(orient='index')
        except FileNotFoundError:
            print(f"ファイル {file_path} が見つからなかったぜ。")
            return None


    def get_df(self, csvname, key, value, column):
        """
        気になる辞書データの要素を拾い出すにはこのメソッドを使うんだぜ｡。
        指定されたキーと値を元に辞書の中から目当ての情報を引きずり出す作業だ。

        例えば、'NOTFOUND'っていう状態の説明が見たいなら、
        状態名が'NOTFOUND'にぴったり合う行をルートアウトして、そこから説明列のデータを引っこ抜くんだ。

        探しているものが見つからなかったら空の文字列を返して、何か変なことが起こっていたら'Error'って返すから頼りにしてくれ。
        Args:
            dict_name (str): 調べる辞書の名前。
            key (str): 辿り着きたい情報のあるキー名だ。これがあるおかげで手がかりになる。
            value (str): 目指す値。この値と一致する行を特定する。
            column (str): このキーからデータをひっぱり出す。
        Returns:
            str: 発掘されたデータ。もしなにもなかったら空の文字列、何か不具合があれば'Error'とする。
        Examples:
            こんな感じで使うんだ：get_value_from_dict("status_descriptions", "状態名", "NOTFOUND", "説明")
            この例なら、'NOTFOUND'という状態に対する説明をくれてやる。
        """
        try:
            # CSVManagerの辞書からデータフレームを取得
            dataframe = pd.DataFrame(self.csvdatas[csvname])
            
            # データフレームから値を取得
            prompt = dataframe.loc[dataframe[key] == value, column].fillna("").values[0]
        except KeyError as e:
            print(f"Error: {csvname}: 指定したキー '{key}' または列 '{column}' で '{value}' が無いぞ。{e}")
            return "Error"
        except IndexError as e:
            print(f"Error: {csvname}: 指定したインデックスが範囲外。{e}")
            return "Error"
        except pd.errors.DataError as e:
            print(f"Error: {csvname}: データ処理に関するエラー。{e}")
            return "Error"
        except Exception as e:
            print(f"不明な他のエラー: {e}")
            return "Error"
        return prompt


    def get_df_2key(self, csvname, key, value, subkey, subvalue, column):
        """
        辞書から条件にピッタリ合ったデータを探り出すなら、このメソッドが役に立つぜ。
        ちゃんとした2つのキーとその対応する値を基にして、賢くデータを掘り出してくるんだ。

        キーとサブキー、それに一致する値を指定することで、要求された情報を辞書の中から見つけ出す。
        まるでダブルロックされた秘宝を解き放つような感じさ。
        Args:
            csvname (str): 調べたい辞書の名前だ。データの海の中でのガイド役になる。
            key (str): メインキーの列名。
            value (str): メインキーの列におけるターゲットとなる値。
            subkey (str): サブキーの列名だ。
            subvalue (str): サブキーの列におけるターゲットとなる値。
            column (str): 結果的に値を取得したい列の名称。
        Returns:
            str: 探し出された報酬。条件にマッチするものが無ければ空文字列、何かおかしい時は'Error'を返す。
        """
        try:
            # CSVManagerの辞書からデータフレームを取得
            dataframe = pd.DataFrame(self.csvdatas[csvname])

            # keyとvalueおよびsubkeyとsubvalueに一致するレコードをフィルタリングして、指定されたcolumnの値を取得
            prompt = next((item[column] for item in dataframe if item[key] == value and item[subkey] == subvalue), "")
        except KeyError as e:
            print(f"Error: {csvname}: キー'{key}'か'{subkey}'、または列'{column}' で '{value}' が無いぞ。{e}")
            return "Error"
        except IndexError as e:
            print(f"Error: {csvname}: 条件'{key} = {value}' かつ '{subkey} = {subvalue}' を満たすデータが見つからなかった - {e}")
            return "Error"
        except Exception as e:
            print(f"予期せぬエラー発生：{e}")
            return "Error"

        # 成功した場合、見つかったプロンプトを返す
        return prompt

    def add_csv(self, csvname1, csvname2):
        """
        2つの辞書を結合して、連番キーを持つ新しい辞書を作成するメソッドだ。
        元の辞書のキーは無視して、新しい単一の辞書で連番のキーを割り当てるぞ。

        Args:
            dict1 (dict): 結合する最初の辞書。
            dict2 (dict): 結合する2番目の辞書。

        Returns:
            dict: 連番キーを持つ新しい辞書。

        注意:
            元の辞書のキーは使用せず、新しい辞書は連番のキーにする。
        """
        data1 = self.read_csv(csvname1)
        data2 = self.read_csv(csvname2)
        combined_dict = data1.copy()  # dict1の内容をコピー
        combined_dict.update(data2)  # dict2の内容を組み込む
        return combined_dict


    def chikan(self, text):
        """置換機能
        文字列中に%で囲まれた部分があればreplacelist.csvに基づいて置換する機能

        Args:
            text (str): プロンプト
        Returns:
            text (str): 置換後プロンプト
        """
        csvname, _ = self.find_csv_path('replacelist.csv')
        # 正規表現で置換対象("%"で挟まれた文字列)をリスト化
        置換対象 = re.findall('%.*?%', text)
        if len(置換対象) > 0:
            # 見つかった置換対象リストの数だけ繰り返し
            for chi in 置換対象:
                # %抜きの文字列でcsvを検索する
                csv参照用 = chi.strip("%")
                text = re.sub(chi, self.get_df(csvname, "置換前", csv参照用, "置換後"), text)
                # get_dfがエラーを出した場合、文字列"Error"に置換される
        return text


    # DictをCSVに出力する
    def write_dict_to_csv(self, file_name, data_dict, headers=None, is_nested_dict=True):
        """
        辞書を渡すと、その内容をCSVファイルに転写してくれる便利な機能だ。
        わたしたちが蓄えてきたデータの宝庫を、世の中に分かち合うためには欠かせない手順さ。

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