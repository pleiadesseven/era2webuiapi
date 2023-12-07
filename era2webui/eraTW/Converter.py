# #eraTWってTEXTLOGで吐き出した変数そのまま使いにくいぞ
# #取得した変数を引数に使える形に変更するコンバーター
# #関数名はTWのERBとさして変わりがないぜ
from sub import CSVManager
csvm = CSVManager()


# 特定のオブジェクトの情報を取得する関数
# @get_str 関数の実装
def get_str(obj_manager, class_name, object_id, attribute_name):
    class_data = {}
    for key, value in obj_manager.existence.items():
        if class_name == "不明なカテゴリー":
            break
        if class_name in key: 
            class_data = value
            break  # 該当するクラス名が見つかったらループを抜ける
    
    object_data = class_data.get(object_id, {})
    if not isinstance(object_data, dict):
        object_data = {}  # 辞書型でなければ空の辞書を使用
    return object_data.get(attribute_name, "データが見つかりません")
    
    
class ObjExistenceManager:
    def __init__(self):
        self.existence = {}       #後で整理する
        self.clothcsv = {}        
        self.category_mapping = {}#装備カテゴリ 
        self.equipcategory = {}
        self.display_part = {}    #表示部位
        self.equipname = {}       #装備名
        self.equip_position = {}  #装備部位
        self.clothdata_from_csv()
        self.load_equipname()
        self.load_equipcategory()
        self.load_display_part()
        self.integrate_display_part()
        self.make_all_class_list()
        self.add_data_from_cloth()
        self.integrate_category()

    def make_all_class_list(self):
        #キャラは1万､それ以外は500
        self.set_list_exist("キャラデータ", 0, 10000)
        self.set_list_exist("キャラリスト", 0, 500)
        self.set_list_exist("衣装セット", 0, 500)
        self.set_list_exist("腕部装束", 0, 500)
        self.set_list_exist("頭装備", 0, 500)
        self.set_list_exist("着物", 0, 500)
        self.set_list_exist("上半身上着_はだけ不可", 0, 500)
        self.set_list_exist("上半身上着_はだけ可能", 0, 500)
        self.set_list_exist("上半身下着_はだけ不可", 0, 500)
        self.set_list_exist("上半身下着_はだけ可能", 0, 500)
        self.set_list_exist("靴下", 0, 500)
        self.set_list_exist("靴", 0, 500)
        self.set_list_exist("外衣", 0, 500)
        self.set_list_exist("下半身下着_ずらし不可", 0, 500)
        self.set_list_exist("下半身下着_ずらし可能", 0, 500)
        self.set_list_exist("ワンピース", 0, 500)
        self.set_list_exist("レオタード", 0, 500)
        self.set_list_exist("ボディースーツ", 0, 500)
        self.set_list_exist("その他衣装", 0, 500)
        self.set_list_exist("ズボン", 0, 500)
        self.set_list_exist("スカート", 0, 500)
        self.set_list_exist("アクセサリ", 0, 500)
        self.set_list_exist("一般依頼", 0, 500)
        self.set_list_exist("FreeAct", 0, 500)
        self.set_list_exist("酒データ", 0, 500)



    def clothdata_from_csv(self):
        data = csvm.read_csv("Cloth.csv")
        # 空の辞書を用意する
        all_data = {}

        for item in data:
            # 各行のデータを取得
            key = item.get('e2wNO')  # 'e2wNO' をキーとして使用する
            if key:
                # 各行の辞書を辞書に追加する
                all_data[key] = item

        # 統合した辞書をインスタンス変数に格納
        self.clothcsv = all_data

    # display_part 辞書に(表示部位:n)のCSVデータを追加
    def load_display_part(self):
        display_part_list = csvm.read_csv('display_part.csv')
        # CSVデータを辞書に追加
        self.display_part = {item['display_part_no']: item['display_part'] for item in display_part_list}

    #equipname 辞書にequipname.csvを登録
    def load_equipname(self):
        equipname_list = csvm.read_csv('equipname.csv')
        self.equipname = {item['position_no']: item['equipname'] for item in equipname_list}

    #equipcategory 辞書にequip_name,categoryを追加
    def load_equipcategory(self):
        category_list = csvm.read_csv('equipcategory.csv')
        self.equipcategory = {item['equip_name']: item['category'] for item in category_list}

    
    #class_nameに対応する空の辞書データを作成
    def set_list_exist(self, class_name, obj_first, obj_last):
        if class_name not in self.existence:
            self.existence[class_name] = {}
        for obj_id in range(obj_first, obj_last + 1):
            self.existence[class_name][obj_id] = False  # または適切な初期値


    def add_or_update_data(self, class_name, obj_id, data):
        if class_name not in self.existence:
            # class_name が存在しない場合、新しいカテゴリとして追加
            self.existence[class_name] = {}
        # obj_id に対応するデータを追加または更新
        self.existence[class_name][obj_id] = data


    def add_data_from_cloth(self):
        # self.cloth のデータを self.existence に追加または更新
        for item in self.clothcsv.values():
            equippart = item.get("装備部位")
            if not equippart:
                continue  # 装備部位がない場合はスキップ
            
            equipname = item.get("衣類名")
            category = item.get("カテゴリ")
            if not category:
                category = self.get_category_mapping(equippart)
            category_no = item.get("カテゴリ内番号", None)
        
            if category is not None and category_no is not None:
                self.add_or_update_data(category, category_no, equipname)


    #該当番号の表示部位の文字列を返す (表示部位:LOCAL)
    def get_display_part(self, part_no):
        # display_part辞書から部位番号に対応する表示部位を取得
        return self.display_part.get(str(part_no), -1)  # 辞書に部位番号がなければ-1を返す


    def get_equip_position(self, display_part):
        #next() 関数は、リストや文字列などの要素を順番に取得
        return next((key for key, value in self.equipname.items() if value == display_part), None)


    #装備部位の番号から該当する衣装カテゴリを返す
    def clothes_parts_to_category(self, get_equip_position_no):
        return self.category_mapping.get(get_equip_position_no, "不明なカテゴリー")


    def integrate_display_part(self):
        for key, value in self.clothcsv.items():
            cloth_name = value.get("衣類名")
            for display_part_no, display_part_name in self.display_part.items():
                if cloth_name == display_part_name:
                    # 表示部位名が一致する場合、表示部位番号と名前をdisplay_part辞書に追加
                    value['表示部位NO'] = display_part_no
                    value['表示部位'] = display_part_name


    #装備部位かからカテゴリの文字列を返す
    def get_category_mapping(self, equippart):
        # display_part辞書から部位番号に対応する表示部位を取得
        return self.category_mapping.get(str(equippart), -1)  # 辞書に部位番号がなければ-1を返す
    
    #equipcategory
    def integrate_category(self):
        category_mapping = {} #一助保存用の空辞書
        for equip_name, category in self.equipcategory.items():
            # equipname 辞書で装備名に対応する部位番号を探す
            for position_no, name in self.equipname.items():
                if name == equip_name:
                    # 部位番号とカテゴリの対応関係を新しい辞書に追加
                    category_mapping[position_no] = category
        # 更新した category_mapping をインスタンス変数に格納
        self.category_mapping = category_mapping
    
    
    def get_cloth_name(self, position_no, equip_no_position):
    # 装備部位に基づいてカテゴリを取得
        category = self.clothes_parts_to_category(position_no)

        # カテゴリと装備部位番号に基づいて衣装の名前を取得
        attribute_name = "衣類名"
        cloth_name = get_str(self,category, equip_no_position, attribute_name)
        return cloth_name


    # 登録されたデータを全て表示するメソッド
    def display_all_data(self):
        for key, value in self.existence.items():
            print(f"Key: {key}, Value: {value}")


    #クラス辞書をCSVに出力 デバック用
    def export_to_csv(self):
        # existence.csv の書き出し
        csvm.write_dict_to_csv('existence.csv', self.clothcsv, is_nested_dict=True)
        # clothcsv.csv の書き出し
        csvm.write_dict_to_csv('clothcsv.csv', self.clothcsv, is_nested_dict=True)
        # category_mapping.csv の書き出し
        csvm.write_dict_to_csv('category_mapping.csv', self.category_mapping, headers=None, is_nested_dict=False)
        # display_part.csv の書き出し
        csvm.write_dict_to_csv('display_part.csv', self.display_part, headers=None, is_nested_dict=False)
        # equip_position.csv の書き出し
        csvm.write_dict_to_csv('equip_position.csv', self.equip_position, headers=None, is_nested_dict=False)
        # equipname.csv の書き出し
        csvm.write_dict_to_csv('equipname.csv', self.equipname, headers=None, is_nested_dict=False)