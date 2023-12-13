"""
eraTW @SHOW_CLOTH のPython移植版
不完全だが動く
処理フローを理解するために作ったがPromptmakerとかに組み込むには修正箇所多い
"""
from module.savedata_handler import SJHFactory
from module.csv_manager import CSVMFactory 
from eraTW.cloth import get_cloth_name, clothes_parts_to_category, get_display_part, get_equip_position


SAVE_PATH = "H:\\era\\era2webuitest\\eraTW-SD\\sav\\txt00.txt"

# クラスのインスタンス化
save = SJHFactory.create_instance(SAVE_PATH)
csvm = CSVMFactory.get_instance()


def nobura(save):
    return (
        save.get_save('キャラ固有番号') != 0 \
        and not save.get_save("性別") ==2 \
        and save.get_save("上半身下着2") == 0 \
        and save.get_save("上半身下着1") == 0 \
        and save.get_save("ボディースーツ") == 0 \
        and save.get_save("レオタード") == 0
    )


def nopan(save):
    return (
        save.get_save('キャラ固有番号') != 0 \
        and save.get_save("下半身下着2") == 0 \
        and save.get_save("下半身下着1") == 0 \
        and save.get_save("ボディースーツ") == 0 \
        and save.get_save("レオタード") == 0
    )


# 特定の装備部位の衣装名を取得
for i in range(1, 23):
    display_part = get_display_part(i)
    position_no = get_equip_position(display_part)
    category = clothes_parts_to_category(position_no)
    if position_no < 0:
        print(f"存在しない装備部位{position_no}")


    # ノーブラ、ノーパン用の例外処理
    if display_part == "上半身下着1" and nobura(save):
        nobura = True
        print("つけていない")
        continue


    if display_part == "下半身下着1" and nopan(save):
        nopan = True
        print("はいてない")
        continue

    if not save.get_save("EQUIP:NO:装備部位").get(i):
        continue

    #パジャマの処理はあとで考える
    
    if display_part == "下半身下着2":
        #下着の名前は辞書で与えられるのでその最初の辞書のvalueを使う
        _, pantus = next(iter(save.get_save("lower_underwear").items()))
        print(f"{pantus}")
    
    if display_part == "上半身下着1":
        _, bura = next(iter(save.get_save("upper_underwear").items()))
        print(f"{bura}")
    
    # 特定の条件に基づく表示内容の決定
    equip_no_dict = save.get_save("EQUIP:NO:装備部位")
    for j, ene in equip_no_dict.items():
        if ene is None:
            continue
        hyoujinaiyou = get_cloth_name(position_no, ene)
        print(f"{display_part}[{hyoujinaiyou}]")
        break  # 名前を見つけたらループを抜ける