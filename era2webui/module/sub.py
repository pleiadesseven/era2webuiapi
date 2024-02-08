import configparser
import random
import re
import time
from tkinter import filedialog
from module.settings import Settings
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

    # -----生成が行われたかの判定。とりあえずブラウザのtitleで判断。
    # （生成中はタイトルが変わる。"Stable Diffusion"に戻ったら完了）
    # タイトル変化に1秒ほどのラグがあり、1秒未満で完了すると検知できない

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



class ReadConfig:
    """
    # GUI
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


def get_width_and_height(kaizoudo):
    """
    渡された解像度文字列を解釈し、幅と高さの整数値のペアを返します。

    書式は "幅x高さ" で、複数のオプションがある場合はカンマで区切ります。
    また、置換リストを適用し "%文字列%" を特定の値に置換することができます。

    例えば、"512x768,768x512,1024x512" と書かれている場合は、ランダムに一つを選んで
    その解像度を適用します。置換機能も組み込まれているから、柔軟な指定が可能だ。

    Args:
        kaizoudo (str): 解読する解像度を示す文字列です。(%正方形%､%横長%)

    Returns:
        tuple: (幅, 高さ) の形で解像度の数値を返します。
                解読できない場合やエラーがある場合は (0, 0) を返します。

    Raises:
        ValueError: 解像度文字列が不正であるか、数値に変換できない値が含まれている場合。
    """
    # 解像度欄でも置換機能を使えるようにする。%で囲まれた文字列があると置換を試みる。
    #インスタンスはこのメソッドを使うときだけ呼び出す｡毎度だと処理が遅くなる
    from module.csv_manager import CSVMFactory
    csvm = CSVMFactory.get_instance()
    kaizoudo = csvm.chikan(kaizoudo)

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

    # アスペクト比の形式の場合、解像度を計算する｡APIモード限定
    Settings.get_config_ini_api()#暫定でここで処理実際は実行ファイルに書くべきポイント
    if ":" in kaizoudo and Settings.apimode:
        kaizoudo = process_aspect_ratio(kaizoudo)

    # xで分割 (区切り文字としてXと*と×も認める)
    kai = re.split("[xX*×]", kaizoudo)
    # エラー処理2 splitで2要素に分割されなかった場合
    if len(kai) != 2:
        print("解像度取得に失敗。splitで2要素に分割されなかった。解像度変更を中止")
        return 0, 0

    try:
        width = int(kai[0])
        height = int(kai[1])
    except ValueError as e:
        # エラー処理3 splitできたが数値として認識できない場合
        print(f"解像度取得に失敗。splitできたが数値として認識できなかった。詳細:{e}")
        print("解像度変更を中止")
        return 0, 0

    return width, height


def process_aspect_ratio(kaizoudo):
    """SDでよく使うのは 512:768 は 2:3
    短辺を基準に計算することで規定お解像度以下の画像は静止されない
    Args:
        アスペクト比 (str): 16:9 とか

    Returns:
        str: '幅x高'
    """
    import json
    import os
    # 現在のファイルのディレクトリを取得
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 親ディレクトリに移動
    parent_dir = os.path.dirname(current_dir)
    # JSON ファイルのパスを構築
    config_api = os.path.join(parent_dir, 'config.json')

    with open(config_api, 'r') as file:
        config = json.load(file)
        base_width = config.get('width', 512)  # デフォルト値は512
        base_height = config.get('height', 512)  # デフォルト値は512

    # アスペクト比を分割
    width_ratio, height_ratio = map(int, kaizoudo.split(':'))

    if width_ratio < height_ratio:  # 縦長の場合、幅を基準にする
        # 基準となる幅を元に高さを計算
        calculated_height = int(base_width / width_ratio * height_ratio)
        # 解像度を64の倍数に調整
        adjusted_width = (base_width // 64) * 64
        adjusted_height = (calculated_height // 64) * 64
    else:  # 縦長の場合、高さを基準にする
        calculated_width = int(base_height / height_ratio * width_ratio)
        adjusted_width = (calculated_width // 64) * 64
        adjusted_height = (base_height // 64) * 64

    # 計算された解像度を返す
    return f"{adjusted_width}x{adjusted_height}"