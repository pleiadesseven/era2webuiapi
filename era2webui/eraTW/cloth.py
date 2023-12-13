from module.csv_manager import CSVMFactory
csvm = CSVMFactory.get_instance()

# cloth.csvのDataFrameを取得
cloth_df = csvm.csvdatas['cloth.csv']

def get_cloth_name(position_no, equip_no_position):
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
    category = clothes_parts_to_category(position_no)
    # カテゴリと装備部位番号に基づいて衣装の名前を取得
    cloth_name_row = cloth_df[(cloth_df['カテゴリ'] == category) & (cloth_df['カテゴリ内番号'] == equip_no_position)]
    if not cloth_name_row.empty:
            return cloth_name_row['衣類名'].iloc[0]
    else:   
        return '衣類が見つかりません'


def clothes_parts_to_category(get_equip_position_no):
    # データフレームを使用してカテゴリを検索
    category_row = cloth_df[cloth_df['装備部位'] == get_equip_position_no]
    if not category_row.empty:
        return category_row.iloc[0]['カテゴリ']
    else:
        return '不明なカテゴリー'


def get_display_part(part_no):
    """
    該当番号の表示部位の文字列を返す
    (表示部位:LOCAL)
    Args:
        part_no (int): 1~22までの任意の値

    Returns: 
        str: 表示部位
    """
    display_part_row = cloth_df[cloth_df['表示部位NO'] == part_no]
    if not display_part_row.empty:
        return display_part_row.iloc[0]['表示部位']
    else:
        print(f"部位NO {part_no} に対応する表示部位が見つかりません。")
        return '不明な表示部位'

    
def get_equip_position(display_part):
    """
    表示部位から対応する装備部位の番号を返す
    Args:
        display_part (str): 表示部位
    Returns:
        int: 装備部位 番号
    """
    equip_position_row = cloth_df[cloth_df['表示部位'] == display_part]
    if not equip_position_row.empty:
        return equip_position_row.iloc[0]['装備部位']
    else:
        return '不明な装備部位'


