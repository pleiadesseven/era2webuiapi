# #eraTWってTEXTLOGで吐き出した変数そのまま使いにくいぞ
# #取得した変数を引数に使える形に変更するコンバーター
# #関数名はTWのERBとさして変わりがないぜ


from sub import find_csv_path
from sub import load_csv




# 特定のオブジェクトの情報を取得する関数
# @get_str 関数の実装
def get_str(obj_manager, class_name, object_id, attribute_name):
    class_data = obj_manager.existence.get(class_name, {})
    object_data = class_data.get(object_id, {})
    return object_data.get(attribute_name, "データが見つかりません")
    
    
class ObjExistenceManager:
    def __init__(self):
        self.existence = {}
        self.category_mapping = {}

    def set_list_exist(self, class_name, obj_first, obj_last):
        if class_name not in self.existence:
            self.existence[class_name] = {}
        for obj_id in range(obj_first, obj_last + 1):
            self.existence[class_name][obj_id] = False
            
    def add_or_update_data(self, class_name, obj_id, data):
        if class_name not in self.existence:
            self.existence[class_name] = {}
        self.existence[class_name][obj_id] = data


    # 登録されたデータを全て表示するメソッド
    def display_all_data(self):
        for key, value in self.existence.items():
            print(f"Key: {key}, Value: {value}")
            

    def make_all_class_list(self):
        #上限値は1万あれば足るだろう
        self.set_list_exist("キャラデータ", 0, 10000)
        self.set_list_exist("キャラリスト", 0, 10000)
        self.set_list_exist("衣装セット", 0, 10000)
        self.set_list_exist("腕部装束", 0, 10000)
        self.set_list_exist("頭装備", 0, 10000)
        self.set_list_exist("着物", 0, 10000)
        self.set_list_exist("上半身上着_はだけ不可", 0, 10000)
        self.set_list_exist("上半身上着_はだけ可能", 0, 10000)
        self.set_list_exist("上半身下着_はだけ不可", 0, 10000)
        self.set_list_exist("上半身下着_はだけ可能", 0, 10000)
        self.set_list_exist("靴下", 0, 10000)
        self.set_list_exist("靴", 0, 10000)
        self.set_list_exist("外衣", 0, 10000)
        self.set_list_exist("下半身下着_ずらし不可", 0, 10000)
        self.set_list_exist("下半身下着_ずらし可能", 0, 10000)
        self.set_list_exist("レオタード", 0, 10000)
        self.set_list_exist("ボディースーツ", 0, 10000)
        self.set_list_exist("その他衣装", 0, 10000)
        self.set_list_exist("ズボン", 0, 10000)
        self.set_list_exist("スカート", 0, 10000)
        self.set_list_exist("FreeAct", 0, 10000)
        self.set_list_exist("酒データ", 0, 10000)


    def load_data_from_csv(self, file_path):
        data = load_csv(file_path)
        for index, item in enumerate(data):
            if index == 0:  # 最初の行（項目名の行）をスキップ
                continue
            key = index - 1  # 行インデックスから1を引いてキーとして使用
            self.existence[key] = item


    #該当番号の装備部位の文字列を返す (表示部位:LOCAL)
    def get_display_part(self, part_no):
        display_part_csv_path = find_csv_path('display_part.csv')
        
    # 取得したパスでequipname_listを初期化
        display_part_list = load_csv(display_part_csv_path)
        
        part_no_str = str(part_no)  # part_no を文字列に変換
        
        for item in display_part_list:
            if item[0] == part_no_str:  # 引数で渡された番号とキーを比較
                return item[1]  # 対応する表示部位を返す
        return -1  # 要素が見つからない場合は-1を返す 


    #@SHOW_CLOTHES装備部位 = FINDELEMENT(EQUIPNAME, 表示部位:LOCAL) と同じ機能
    def get_equip_position(self, display_part):
        # equipname.csvのパスを取得
        equipname_csv_path = find_csv_path('equipname.csv')

        # 取得したパスでequipname_listを初期化
        equipname_list = load_csv(equipname_csv_path)
        #print (f"equipname_list {equipname_list}")
        for item in equipname_list:
            #print(item)
            # リストの長さが2以上であることを確認
            if len(item) >= 2 and display_part == item[1]:
                return item[0]  # 対応する装備部位番号を返す
        return -1  # 要素が見つからない場合は-1を返す


    #装備部位(get_equip_position)とカテゴリの対応関係をマッピングself.category_mapping = {}に値を格納
    def set_category_mapping(self, position_no):
        equipname_csv_path = find_csv_path('equipname.csv')
        equipname_list = load_csv(equipname_csv_path)
        
        # position_no を文字列に変換
        position_no_str = str(position_no)

        # 引数として渡された position_no が equipname_dict に存在するか確認
        for item in equipname_list:
            if len(item) >= 2 and position_no_str == item[0]:  # 最初の要素（装備部位番号）を確認
                equip_name = item[1]  # 対応する装備名を取得
                if equip_name:  # equip_name が空でないことを確認
                    self.category_mapping[position_no] = self.determine_category(equip_name)
                    return  # 見つかった場合、ループを終了
        raise ValueError(f"存在しない装備部位番号: {position_no}")  # 対応する装備部位番号が見つからない場合


    def determine_category(self, equip_name):
        equip_part_category = equip_name
        # print (f"aaaaaaaaaa{equip_part_category}")
        
        if equip_part_category in ["下半身下着2"]:
            return "パンツ"
        elif equip_part_category in ["着物", "レオタード", "ボディースーツ", "ワンピース"]:
            return "全身衣装"
        elif equip_part_category in ["帽子", "外衣", "腕部装束", "上半身上着1", "上半身上着2", "上半身下着1", "上半身下着2"]:
            return "上半身衣装"
        elif equip_part_category in ["スカート", "ズボン", "靴", "靴下", "下半身下着1"]:
            return "下半身衣装"
        elif equip_part_category in ["アクセサリ", "その他1", "その他2", "その他3"]:
            return "その他衣装"
        elif equip_part_category in ["アクセサリ", "靴", "靴下", "レオタード", "ボディースーツ", "ズボン", "スカート", "ワンピース", "着物", "外衣", "腕部装束"]:
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
            raise ValueError(f"不明な部位: {equip_part_category} 渡された引数: {equip_name}")


    #装備部位の番号から該当する衣装カテゴリを返す
    def clothes_parts_to_category(self, get_equip_position_no):
        return self.category_mapping.get(get_equip_position_no, "不明なカテゴリー")


