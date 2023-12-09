"""
eraTW @SHOW_CLOTH のPython移植版
不完全だが動く
処理フローを理解するために作ったがPromptmakerとかに組み込むには修正箇所多い
"""

from eraTW.Converter import ClothExistenceUpdater
from sub import SaveJSONHandler

SAVE_PATH = "H:\\era\\era2webuitest\\eraTW-SD\\sav\\txt00.txt"

# クラスのインスタンス化
ceu = ClothExistenceUpdater()
save = SaveJSONHandler(SAVE_PATH)


# 特定の装備部位の衣装名を取得
for i in range(1, 23):
    display_part = ceu.get_display_part(i)
    equip_part = ceu.get_equip_position(display_part)
    equip_part_int = int(equip_part)
    if equip_part_int < 0:
        print(f"存在しない装備部位{equip_part_int}")

    if display_part == "上半身下着1":
        items = ["上半身下着2", "上半身下着1", "ボディースーツ", "レオタード"]
        if all(save.get_save(item) == 0 for item in items):
            if save.get_save("上半身下着表示フラグ") == 1:
                print("装備:下着(上)(つけていない)")

            elif save.get_save("下半身下着表示フラグ") == 1:
                print("装備:下着(上)(？？？？？)")

    if display_part == "下半身下着1":
        items = ["下半身下着2", "下半身下着1", "ボディースーツ", "レオタード"]
        if all(save.get_save(item) == 0 for item in items):
            if not save.get_save("上半身下着表示フラグ") and not save.get_save("下半身下着表示フラグ"):
                print("装備:下着　　(？？？？？)")
                continue
            elif not save.get_save("下半身下着表示フラグ"):
                print("装備:下着(下)(？？？？？)")
            else:
                print("装備:下着(下)(はいてない)")

    # パジャマ判定を取得し空白でないCFLAG:NO:パジャマが1である時パジャマの名前を取得
    # あとで直す
    if len(save.get_save('パジャマ判定').get(i, ""))  and not save.get_save('CFLAG:NO:パジャマ'):
        hyoujinaiyou = "パジャマ"  # 仮データeraから名前を直の取得するかはあとで考える

    # 上半身下着の特別な表示処理
    elif display_part == "上半身下着1" and save.get_save('キャラ固有番号') != 0 and not save.get_save("上半身下着表示フラグ"):
        if not save.get_save("下半身下着表示フラグ"):
            continue
        hyoujinaiyou = "？？？？？"

    # 下半身下着の特別な表示処理
    elif display_part == "下半身下着２" and save.get_save('キャラ固有番号') != 0 and not save.get_save("下半身下着表示フラグ"):
        if not save.get_save("上半身下着表示"):
            print("装備:下着　　(？？？？？)")
            continue
        else:
            hyoujinaiyou = "？？？？？"

    else:
        if display_part == "上半身下着1":
            upper_underwear_dict = save.get_save("upper_underwear")
            if upper_underwear_dict:
                # 辞書から最初のキー・値ペアを取得
                clothing_key, clothing_name = next(
                    iter(upper_underwear_dict.items()))
                hyoujinaiyo = clothing_name

        if display_part == "下半身下着2":
            lower_underwear_dict = save.get_save("lower_underwear")
            if lower_underwear_dict:
                # 辞書から最初のキー・値ペアを取得
                clothing_key, clothing_name = next(
                    iter(lower_underwear_dict.items()))
                hyoujinaiyou = clothing_name
        else:
            equip_no_i = save.get_save("EQUIP:NO:表示部位").get(str(i))
            # i に対応するキーが存在しない場合、処理をスキップする
            if equip_no_i is None:
                continue
            hyoujinaiyou = ceu.get_cloth_name(equip_part, equip_no_i)

    print(f"{hyoujinaiyou}")
