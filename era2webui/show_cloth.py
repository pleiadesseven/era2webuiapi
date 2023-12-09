"""
eraTW @SHOW_CLOTH のPython移植版
不完全だが動く
処理フローを理解するために作ったがPromptmakerとかに組み込むには修正箇所多い
"""
import json
from eraTW.Converter import ClothExistenceUpdater
ceu = ClothExistenceUpdater()


# JSONファイルを読み込む関数。ファイルパスを引数とする。
def load_equip_data(file_path):
    """
    テスト用関数､Promptmakerあたりとの整合性はあとでとる
    Args:
        file_path (str): jsonのpath

    Returns:
        dict: JSONの中身
    """
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as file:
            return json.load(file)
    except FileNotFoundError as e:
        print(f"ファイル {file_path} が見つかりません。 {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSONデコードエラーが発生しました: {e}")
        return None


SAVE_PATH = "H:\\era\\era2webuitest\\eraTW-SD\\sav\\txt00.txt"
equip_data = load_equip_data(SAVE_PATH)


# 特定の装備部位の衣装名を取得
for i in range(1, 23):
    display_part = ceu.get_display_part(i)
    equip_part = ceu.get_equip_position(display_part)
    equip_part_int = int(equip_part)
    if equip_part_int < 0:
        print(f"存在しない装備部位{equip_part_int}")

    if display_part == "上半身下着1":
        if all(equip_data.get(item, 0) == 0 for item
                in ["上半身下着２", "上半身下着1", "ボディースーツ", "レオタード", 0]):
            if int(equip_data["上半身下着表示フラグ"]) == 1:
                print("装備:下着(上)[つけていない]")

            elif int(equip_data["下半身下着表示フラグ"]) == 1:
                print("装備:下着(上)[？？？？？]")

    if display_part == "下半身下着1":
        if all(equip_data.get(item, 0) == 0 for item in
                ["下半身下着2", "下半身下着1", "ボディースーツ", "レオタード", 0]):
            if not int(equip_data["上半身下着表示フラグ"]) and not int(equip_data["下半身下着表示フラグ"]):
                print("装備:下着　　[？？？？？]")
                continue
            elif not int(equip_data["下半身下着表示フラグ"]):
                print("装備:下着(下)[？？？？？]")
            else:
                print("装備:下着(下)[はいてない]")

    # パジャマ判定を取得し空白でないCFLAG:NO:パジャマが1である時パジャマの名前を取得
    # あとで直す
    if len(equip_data.get('パジャマ判定', {}).get(i, "")) and not int(equip_data['CFLAG:NO:パジャマ']):
        hyoujinaiyou = "パジャマ"  # 仮データeraから名前を自家の取得するかはあとで考える

    # 上半身下着の特別な表示処理
    elif display_part == "上半身下着1" and int(equip_data['キャラ固有番号']) != 0 and not int(equip_data["上半身下着表示フラグ"]):
        if not int(equip_data["下半身下着表示フラグ"]):
            continue
        hyoujinaiyou = "？？？？？"

    # 下半身下着の特別な表示処理
    elif display_part == "下半身下着２" and int(equip_data['キャラ固有番号']) != 0 and not int(equip_data["下半身下着表示フラグ"]):
        if not int(equip_data["上半身下着表示"]):
            print("装備:下着　　[？？？？？]")
            continue
        else:
            hyoujinaiyou = "？？？？？"

    else:
        if display_part == "上半身下着1":
            upper_underwear_dict = equip_data.get("upper_underwear", {})
            if upper_underwear_dict:
                # 辞書から最初のキー・値ペアを取得
                clothing_key, clothing_name = next(
                    iter(upper_underwear_dict.items()))
                hyoujinaiyo = clothing_name

        if display_part == "下半身下着2":
            lower_underwear_dict = equip_data.get("lower_underwear", {})
            if lower_underwear_dict:
                # 辞書から最初のキー・値ペアを取得
                clothing_key, clothing_name = next(
                    iter(lower_underwear_dict.items()))
                hyoujinaiyou = clothing_name
        else:
            equip_no_i = equip_data.get("EQUIP:NO:表示部位", {}).get(str(i))
            # i に対応するキーが存在しない場合、処理をスキップする
            if equip_no_i is None:
                continue
            hyoujinaiyou = ceu.get_cloth_name(equip_part, equip_no_i)

    print(f"{hyoujinaiyou}")
