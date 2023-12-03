# #eraTWってTEXTLOGで吐き出した変数そのまま使いにくいぞ
# #取得した変数を引数に使える形に変更するコンバーター
# #関数名はTWのERBとさして変わりがないぜ


# find_one_piece_id 関数:
#     ワンピースの名前をピシャリと指定すれば、そのIDをバシッと探し出してくれる便利な関数だ。

# get_str 関数:
#     こいつは、指定したクラス名とオブジェクトID、それに属性名から、必要な文字情報をキュッと取り出してくれるんだ。

# get_obj 関数:
#     この関数は、オブジェクトがちゃんと存在するかどうかをチェックして、大丈夫なら指定された属性のデータをさっと返してくれるぜ。

# get_exist 関数:
#     クラス名とIDがちゃんと合ってるかどうか、これでバッチリ確認できるんだ。

# ObjExistenceManager クラス:
#     これはオブジェクトの存在状態をグッと管理するためのクラスだ。新しいのを作ったり、状態を設定したり、確認したりと、色々できる優れものさ。

# make_int 関数:
#     指定された変数名で整数値をパッと作って、一時変数にポンと入れる関数だぜ。でも、もうある名前を使おうとすると、バン！ってエラーが出るから気をつけてな。
import csv
from sub import find_csv_path
from sub import load_csv
from sub import csvlist


#装備部位の番号から該当する衣装カテゴリを返す
def clothes_parts_to_category(get_equip_position_no):
    # equipname.csvのパスを取得
    equipname_csv_path = find_csv_path('equipname.csv')[1]

    # 取得したパスでequipname_dictを初期化
    equipname_dict = load_csv(equipname_csv_path)

    # カテゴリを取得
    equip_part_data = equipname_dict.get(str(get_equip_position_no))
    if equip_part_data is None:
        return f"不明な装備部位インデックス: {get_equip_position_no}"

    equip_part_category = equip_part_data[0]
    print (f"{equip_part_category}")
    
    if equip_part_category in ["下半身下着2"]:
        return "パンツ"
    elif equip_part_category in ["着物", "レオタード", "ボディスーツ", "ワンピース"]:
        return "全身衣装"
    elif equip_part_category in ["帽子", "外衣", "腕部装束", "上半身上着1", "上半身上着2", "上半身下着1", "上半身下着2"]:
        return "上半身衣装"
    elif equip_part_category in ["スカート", "ズボン", "靴", "靴下", "下半身下着1"]:
        return "下半身衣装"
    elif equip_part_category in ["アクセサリ", "その他1", "その他2", "その他3"]:
        return "その他衣装"
    elif equip_part_category in ["アクセサリ", "靴", "靴下", "レオタード", "ボディスーツ", "ズボン", "スカート", "ワンピース", "着物", "外衣", "腕部装束"]:
        return equip_part_category
    elif equip_part_category == "帽子":
        return "頭装備"
    elif equip_part_category == "下半身下着1":
        return "下半身下着_ずらし不可"
    elif equip_part_category == "下半身下着2":
        return "下半身下着_ずらし可能"
    elif equip_part_category == "上半身下着1":
        return "上半身下着_はだけ不可"
    elif equip_part_category == "上半身下着2":
        return "上半身下着_はだけ可能"
    elif equip_part_category == "上半身上着1":
        return "上半身上着_はだけ不可"
    elif equip_part_category == "上半身上着2":
        return "上半身上着_はだけ可能"
    elif equip_part_category in ["その他1", "その他2", "その他3", "下半身上着"]:
        return "その他衣装"
    else:
        raise ValueError(f"不明な部位: {equip_part_category} 渡された引数: {get_equip_position_no}")


#@SHOW_CLOTHES装備部位と同じ機能
def get_equip_position(display_part):
    # equipname.csvのパスを取得
    equipname_csv_path = find_csv_path('equipname.csv')[1]

    # 取得したパスでequipname_listを初期化
    equipname_dict = load_csv(equipname_csv_path)
    #print (f"equipname_list {equipname_dict}")
    for key, value in equipname_dict.items():
        if display_part in value:
            return key
    return -1  # 要素が見つからない場合は-1を返す
    
    

# 特定のオブジェクトの情報を取得する関数
# get_str 関数の実装
def get_str(csv_data, object_id, object_data):
    equipname_csv_path = find_csv_path('equipname.csv')[1]
    equipname_dict = load_csv(equipname_csv_path)
    obj = csv_data.get(object_id)
    if obj:
            return obj.get(object_data, "データが見つかりません")
    else:
        return "オブジェクトが見つかりません"
        
def get_str(class_name, object_id, object_data):
    # class_nameに基づいて対応するCSVファイルを特定
    csv_path = find_csv_path("{class_name}.csv") 

    # CSVファイルを読み込む
    csv_data = load_csv(csv_path)

    # 指定されたobject_idでデータを取得
    obj = csv_data.get(object_id)
    if obj:
        # object_dataに対応する値を取得
        return obj.get(object_data, "データが見つかりません")
    else:
        return "オブジェクトが見つかりません"