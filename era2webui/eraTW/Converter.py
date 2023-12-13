"""
eraTWってTEXTLOGで吐き出した変数そのまま使いにくいぞ
取得した変数を引数に使える形に変更するコンバーター
関数名はTWのERBとさして変わりがないぜ
"""
from module.csv_manager import CSVMFactory
csvm = CSVMFactory.get_instance()

# 特定のオブジェクトの情報を取得する関数
# @get_str 関数の実装
def get_str(obj_manager, class_name, object_id, attribute_name):
    """
    objectのSTR情報の参照
    class_name (str):OBJの名前 オブジェクトのカテゴリ make_all_class_list で登録
    object_id (int): オブジェクトのID
    attribute_name (str): ;参照したい情報の名前（例：名前）
    """
    class_data = {}
    for key, value in obj_manager.existence.items():
        if class_name == "不明なカテゴリー":
            break
        if class_name in key:
            class_data = value
            break  # 該当するクラス名が見つかったらループを抜ける

    object_data = class_data.get(int(object_id), {})
    if not isinstance(object_data, dict):
        object_data = {}  # 辞書型でなければ空の辞書を使用
    return object_data.get(attribute_name, "データが見つかりません")


class ObjExistenceManager:
    """
    オブジェクトの管理クラス
    """
    def __init__(self):
        print("ObjExistenceManagerの__init__が実行された")  # デバッグ用
        self.existence = {}  # 後で整理する
        self.clothcsv = {}
        self.category_mapping = {}  # 装備カテゴリ
        self.equipcategory = {}
        self.display_part = {}  # 表示部位
        self.equipname = {}  # 装備名
        self.make_all_class_list()
        self.clothdata_from_csv()
        self.load_equipname()
        self.load_equipcategory()
        self.load_display_part()
        self.integrate_display_part()
        self.integrate_category()

    def add_or_update_data(self, class_name, obj_id, key, value):
        """
        objectのSTR情報の追加
            class_name (str):OBJの名前 オブジェクトのカテゴリ make_all_class_list で登録
            key (str): 追加または更新したい情報のキー (例:名前 ､衣類名など)
            value (str): 追加または更新したい情報の値 (例:帽子 ､指輪など)
        """
        if class_name not in self.existence:
            # class_name が存在しない場合、新しいカテゴリとして追加
            self.existence[class_name] = {}

        if obj_id not in self.existence[class_name]:
            # obj_id が存在しない場合、新しいオブジェクトIDとして追加
            self.existence[class_name][obj_id] = {}

        # obj_id に対応するデータ（キーと値のペア）を追加または更新
        self.existence[class_name][obj_id][key] = value
        # # デバッグ
        # print(
        #     f'追加されたデータ カテゴリ:{class_name} オブジェクトID:{obj_id} キー:{key} 値:{value}')


    def set_list_exist(self, class_name, obj_first, obj_last):
        """
        class_nameをkeyにexistenceにFalseで埋めたの辞書を作成する
        Args:
            class_name (str): クラス名 カテゴリ
            obj_first (int): 最小値
            obj_last (int):  最大値
        """
        if class_name not in self.existence:
            self.existence[class_name] = {}
        for obj_id in range(obj_first, obj_last + 1):
            # eraTWにならってFalseで埋めると問題が出るのでからの辞書で埋める
            self.existence[class_name][obj_id] = {}  # または適切な初期値
            # print(f'追加されたカテゴリ {class_name} をexistenceにネストしました ') #デバッグ


    def make_all_class_list(self):
        """
        値は暫定
        eraTWだと最大は160ほど
        """
        MAX_CHARACTERS = 10000
        MAX_ITEMS = 500
        # キャラは1万､それ以外は500
        self.set_list_exist("キャラデータ", 0, MAX_CHARACTERS)
        self.set_list_exist("キャラリスト", 0, MAX_ITEMS)
        self.set_list_exist("衣装セット", 0, MAX_ITEMS)
        self.set_list_exist("腕部装束", 0, MAX_ITEMS)
        self.set_list_exist("頭装備", 0, MAX_ITEMS)
        self.set_list_exist("着物", 0, MAX_ITEMS)
        self.set_list_exist("上半身上着_はだけ不可", 0, MAX_ITEMS)
        self.set_list_exist("上半身上着_はだけ可能", 0, MAX_ITEMS)
        self.set_list_exist("上半身下着_はだけ不可", 0, MAX_ITEMS)
        self.set_list_exist("上半身下着_はだけ可能", 0, MAX_ITEMS)
        self.set_list_exist("靴下", 0, MAX_ITEMS)
        self.set_list_exist("靴", 0, MAX_ITEMS)
        self.set_list_exist("外衣", 0, MAX_ITEMS)
        self.set_list_exist("下半身下着_ずらし不可", 0, MAX_ITEMS)
        self.set_list_exist("下半身下着_ずらし可能", 0, MAX_ITEMS)
        self.set_list_exist("ワンピース", 0, MAX_ITEMS)
        self.set_list_exist("レオタード", 0, MAX_ITEMS)
        self.set_list_exist("ボディースーツ", 0, MAX_ITEMS)
        self.set_list_exist("その他衣装", 0, MAX_ITEMS)
        self.set_list_exist("ズボン", 0, MAX_ITEMS)
        self.set_list_exist("スカート", 0, MAX_ITEMS)
        self.set_list_exist("アクセサリ", 0, MAX_ITEMS)
        self.set_list_exist("一般依頼", 0, MAX_ITEMS)
        self.set_list_exist("FreeAct", 0, MAX_ITEMS)
        self.set_list_exist("酒データ", 0, MAX_ITEMS)


    def clothdata_from_csv(self):
        """
        Cloth.csvを取り込む
        """
        data = csvm.read_csv("Cloth.csv")  # CSVManagerのread_csvを使用 受け取るのはパンダのデータフレーム
        all_data = {}
        for _, item in data.iterrows():  # Pandasの行ごとにループ
            # 各行のデータを取得
            key = item['e2wNO']  # 'e2wNO' をキーとして使用する
            if key:
                # 各行の辞書を辞書に追加する
                all_data[key] = item.to_dict()
        # 統合した辞書をインスタンス変数に格納
        self.clothcsv = all_data


    def load_display_part(self):
        """
        display_part 辞書に(表示部位:n)のCSVデータを追加
        """
        display_part_list = csvm.read_csv('display_part.csv')
        # データフレームを辞書に追加
        self.display_part = {row['display_part_no']: row['display_part'] 
                             for _, row in display_part_list.iterrows()}

    def load_equipname(self):
        """
        equipname 辞書にequipname.csvを登録
        """
        equipname_list = csvm.read_csv('equipname.csv')
        self.equipname = {row['position_no']: row['equipname'] 
                             for _, row in equipname_list.iterrows()}

    def load_equipcategory(self):
        """
        equipcategory 辞書に装備部位名とカテゴリの対応を追加
        """
        category_list = csvm.read_csv('equipcategory.csv')
        self.equipcategory = {row['equip_name']: row['category'] 
                             for _, row in category_list.iterrows()}


    def get_display_part(self, part_no):
        """
        該当番号の表示部位の文字列を返す
        (表示部位:LOCAL)
        Args:
            part_no (int): 1~22までの任意の値

        Returns: 
            str: 表示部位
        """
        # display_part辞書から部位番号に対応する表示部位を取得
        return self.display_part.get(part_no, -1)  # 辞書に部位番号がなければ-1を返す


    def get_equip_position(self, display_part):
        """
        表示部位から対応する装備部位の番号を返す
        Args:
            display_part (str): 表示部位
        Returns:
            int: 装備部位 番号
        """

        # next() 関数は、リストや文字列などの要素を順番に取得
        return next((key for key, value in self.equipname.items() if value == display_part), None)


    def clothes_parts_to_category(self, get_equip_position_no):
        """
        装備部位を受け取ってそのカテゴリーを返す
        Args:
            get_equip_position_no (int): 装備部位
        Returns:
            str: カテゴリ
        """
        return self.category_mapping.get(get_equip_position_no, "不明なカテゴリー")


    def integrate_display_part(self):
        """
        clothcsvの更新
        clothcsvから衣類名を取り出しdisplay_partと突き合わせる
        一致したら clothcsv に保存
        """
        for _, value in self.clothcsv.items():
            cloth_name = value.get("衣類名")
            for display_part_no, display_part_name in self.display_part.items():
                if cloth_name == display_part_name:
                    value['表示部位NO'] = display_part_no
                    value['表示部位'] = display_part_name


    def get_category(self, equippart):
        """
        display_part辞書から部位番号に対応する表示部位を取得
        Args:
            equippart (int): 装備部位
        Returns:
            Str: カテゴリ
        """
        return self.category_mapping.get(str(equippart), -1)


    def integrate_category(self):
        """
        equipcategoryの名前とequipnameの名前を突き合わせる
        一致したらequipnameの番号をKeyにしてcategory_mappingに保存
        """
        category_mapping = {}  # 一助保存用の空辞書
        for equip_name, category in self.equipcategory.items():
            # equipname 辞書で装備名に対応する装備部位を探す
            for position_no, name in self.equipname.items():
                if name == equip_name:
                    # 装備部位とカテゴリの対応関係を新しい辞書に追加
                    category_mapping[position_no] = category
        # 更新した category_mapping をインスタンス変数に格納
        self.category_mapping = category_mapping


    def get_cloth_name(self, position_no, equip_no_position):
        """
        (装備部位,EQUIP:NO:装備部位)の装備名取得
        Args:
            position_no (int): 装備部位
            equip_no_position (int): EQUIP:NO:装備部位 
                                    これはeraから直に吐き出させる
        Returns:
            str: カテゴリ
        """
        # 装備部位に基づいてカテゴリを取得
        category = self.clothes_parts_to_category(position_no)
        # カテゴリと装備部位番号に基づいて衣装の名前を取得
        attribute_name = "衣類名"
        cloth_name = get_str(self, category, equip_no_position, attribute_name)
        return cloth_name


    def display_all_data(self):
        """
        ## 登録されたデータを全て表示するメソッド
        """
        for key, value in self.existence.items():
            print(f"Key: {key}, Value: {value}")


    def export_to_csv(self):
        """
        クラス辞書をCSVに出力 デバック用
        """
        # existence.csv の書き出し
        csvm.write_dict_to_csv(
            'existence.csv', self.clothcsv, is_nested_dict=True)
        # clothcsv.csv の書き出し
        csvm.write_dict_to_csv(
            'clothcsv.csv', self.clothcsv, is_nested_dict=True)
        # category_mapping.csv の書き出し
        csvm.write_dict_to_csv(
            'category_mapping.csv', self.category_mapping, headers=None, is_nested_dict=False)
        # display_part.csv の書き出し
        csvm.write_dict_to_csv(
            'display_part.csv', self.display_part, headers=None, is_nested_dict=False)
        # equipname.csv の書き出し
        csvm.write_dict_to_csv(
            'equipname.csv', self.equipname, headers=None, is_nested_dict=False)


class ClothDataProcessor(ObjExistenceManager):
    """
    衣類データの処理用クラス
    clothcsvに他の表のデータを集積する
    """

    def __init__(self):
        print("ClothDataProcessorの__init__が実行された")  # デバッグ
        super().__init__()
        self.add_display_partandno()
        self.add_equip_position()
        self.add_equip_category()


    def add_display_partandno(self):
        """
        clothcsv 辞書の各要素に対して、以下の処理を行う。
        1. 各要素から "衣類名" を取得する。
        2. display_part 辞書を使って、"衣類名" と同じ "表示部位" とその番号（表示部位:LOCALのLOCAL部分）を検索する。
        3. 見つかった場合、その "表示部位" と "表示部位NO" を clothcsv の該当する要素に追加する
        """
        for _, value in self.clothcsv.items():
            cloth_name = value.get("衣類名")

            # 対応する表示部位を探す
            display_part_no = next((part_no for part_no, part_name in self.display_part.items(
            ) if part_name == cloth_name), None)

            if display_part_no:
                # 表示部位の情報を clothcsv のアイテムに追加
                value['表示部位NO'] = display_part_no
                value['表示部位'] = self.display_part.get(
                    display_part_no, "不明な表示部位")


    def add_equip_position(self):
        """
        装備部位 = FINDELEMENT(EQUIPNAME, 表示部位:LOCAL)
        clothcsv 辞書の各要素に対して、以下の処理を行う。
        1. 各要素から "表示部位" を取得する。
        2. equipname 辞書を使って、"表示部位" と同じ "表示部位" の番号を検索する。
        3. 見つかった場合、 "装備部位" として clothcsv の該当する要素に追加する
        """
        for _, value in self.clothcsv.items():
            display_part = value.get("表示部位")

            equip_position_no = next((equip_no for equip_no, equip_name in self.equipname.items(
            ) if equip_name == display_part), None)

            if equip_position_no:
                value["装備部位"] = equip_position_no


    def add_equip_category(self):
        """
        @CLOTHES_PARTS_TO_CATEGORY(EQUIPNAME:(装備部位)

        clothcsv 辞書の各要素に対して、以下の処理を行う。
        1. 各要素から "装備部位" を取得する。
        2. "装備部位" の番号をclothes_parts_to_categoryに渡して "カテゴリ" を得る
        3. 値を "カテゴリ" の項目に追加する
        """
        for _, value in self.clothcsv.items():
            position_no = value.get("装備部位")

            category = self.clothes_parts_to_category(position_no)
            if category:
                value["カテゴリ"] = category


class ClothExistenceUpdater(ClothDataProcessor):
    """
    ClothDataProcessorで統合されたclothcsvを
    get_strが使えるようにexistenceに追加
    """

    def __init__(self):
        print("ClothExistenceUpdaterの__init__が実行された")  # デバッグ
        super().__init__()
        self.update_existence()


    def update_existence(self):
        """
        clothcsvのカテゴリ列を参照する
        カテゴリのValueをkeyにexistenceに名前とカテゴリ内番号を登録
        """
        for _, cloth in self.clothcsv.items():
            category = cloth.get("カテゴリ")
            obj_id = cloth.get("カテゴリ内番号")
            cloth_name = cloth.get("衣類名")
            label = "衣類名"
            # obj_id が数値でないなら処理をスキップ
            if obj_id is not None and str(obj_id).isdigit():
                # 文字列から整数へ変換しないと登録されない
                self.add_or_update_data(
                    category, int(obj_id), label, cloth_name)
