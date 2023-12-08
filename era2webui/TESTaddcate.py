import json
from eraTW.Converter import ClothExistenceUpdater
ceu = ClothExistenceUpdater()


# JSONファイルを読み込む関数。ファイルパスを引数とする。
def load_equip_data(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as file:
            return json.load(file)
    except FileNotFoundError as e:
        print(f"ファイル {file_path} が見つかりません。 {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSONデコードエラーが発生しました: {e}")
        return None

file_path = "H:\\era\\era2webuitest\\eraTW-SD\\sav\\txt00.txt"
equip_data = load_equip_data(file_path)

# 特定の装備部位の衣装名を取得
for i in range(1, 23):
    display_part = ceu.get_display_part(i)
    equip_part = ceu.get_equip_position(display_part)
    equip_part_int = int(equip_part)
    if equip_part_int < 0:
        raise Exception(f"存在しない装備部位{equip_part_int}")
    
    if display_part == "上半身下着1":
        if all(equip_data.get(item, 0) == 0 for item in 
                ["上半身下着２", "上半身下着1", "ボディースーツ", "レオタード", 0]):
            if equip_data["上半身下着表示フラグ"] == 1:
                print(f"装備:下着(上)[つけていない]")
        
            elif equip_data["下半身下着表示フラグ"] == 1:
                print(f"装備:下着(上)[？？？？？]")

    if display_part == "下半身下着1":
        if not equip_data["上半身下着表示フラグ"] and not equip_data["下半身下着表示フラグ"]:
            print(f"装備:下着　　[？？？？？]")
            continue
        elif not equip_data["下半身下着表示フラグ"]:
            print(f"装備:下着(下)[？？？？？]")
        else:
            print(f"装備:下着(下)[はいてない]")
    
        # 衣装の名前を取得し、パジャマでない場合はその名前を表示内容とする
    if len(equip_data.get("CSTR", {}).get(f"C_ID:{i + 50}", "")) and not equip_data.get("CFLAG", {}).get("C_ID:パジャマ", False):
        hyoujinaiyou = equip_data["CSTR"][f"C_ID:{equip_part + 50}"]

    # 上半身下着の特別な表示処理
    elif display_part  == "上半身下着1" and int(equip_data['キャラ固有番号']) != 0 and not equip_data["上半身下着表示フラグ"]:
        if not equip_data["下半身下着表示フラグ"]:
            continue
        hyoujinaiyou = "？？？？？"

    # 下半身下着の特別な表示処理
    elif display_part == "下半身下着２" and int(equip_data['キャラ固有番号']) != 0 and not equip_data["下半身下着表示フラグ"]:
        if not equip_data["上半身下着表示"]:
            print(f"装備:下着　　[？？？？？]")
            continue
        else:
            hyoujinaiyou = "？？？？？"
    
    else:
        if display_part == "上半身下着1":
            upper_underwear_dict = equip_data.get("upper_underwear", {})
            if upper_underwear_dict:
                # 辞書から最初のキー・値ペアを取得
                clothing_key, clothing_name = next(iter(upper_underwear_dict.items()))
                hyoujinaiyo = clothing_name
                
        if display_part == "下半身下着2":
            lower_underwear_dict = equip_data.get("lower_underwear", {})
            if lower_underwear_dict:
                # 辞書から最初のキー・値ペアを取得
                clothing_key, clothing_name = next(iter(lower_underwear_dict.items()))
                hyoujinaiyou = clothing_name
        else:
            equip_no_i = equip_data.get("EQUIP:NO:表示部位", {}).get(str(i))
            # i に対応するキーが存在しない場合、処理をスキップする
            if equip_no_i is None:
                continue
            hyoujinaiyou = ceu.get_cloth_name(equip_part, equip_no_i)
            
    print (f"{hyoujinaiyou}")







#     # ノーブラ、ノーパン用の例外処理
#     if local == "上半身下着1" and TALENT["性別"] != 2 and all(EQUIP["上半身下着２"] == 0, EQUIP["上半身下着1"] == 0, EQUIP["ボディースーツ"] == 0, EQUIP["レオタード"] == 0, EQUIP[0] == 0):
#         # 上半身下着の表示処理
#         pass
#     # 他の条件式に関する処理...

#     # 装備部位によって表示内容を設定
#     if not EQUIP["装備部位"]:
#         continue
#     elif len(CSTR["装備部位"]) and not CFLAG["パジャマ"]:
#         表示内容 = CSTR[f"{50 + equip_part}"]
#     # 他の条件式に関する処理...

#     print(f"{表示ラベル[local]}[{表示内容}]")
# ;衣装系の表示関数
# @SHOW_CLOTHES(C_ID, TYPE, ID)
# #DIM  C_ID
# #DIMS TYPE
# #DIM  ID
# #DIM  装備部位
# #DIM  CLOTHES
# #DIMS 表示内容

# 	FOR LOCAL, 1, 23
# 		;装備部位のID取得
# 		装備部位 = FINDELEMENT(EQUIPNAME, 表示部位:LOCAL)
# 		SIF 装備部位 < 0
# 			THROW 存在しない装備部位%表示部位:LOCAL%
		
# 		;ノーブラ、ノーパン用の例外処理
# 		;ここから
# 		IF 表示部位:LOCAL == "上半身下着1" && TALENT:C_ID:性別 != 2 && EQUIP:C_ID:上半身下着２ == 0 && EQUIP:C_ID:上半身下着1 == 0 && EQUIP:C_ID:ボディースーツ == 0 && EQUIP:C_ID:レオタード == 0 && EQUIP:C_ID:0
# 			IF 上半身下着表示(C_ID) == 1
# 				STR:(12000 + LOCAL) = つけていない
# 				PRINTFORML 　装備:下着(上)[つけていない]
# 			ELSEIF 下半身下着表示(C_ID) == 1
# 				PRINTFORML 　装備:下着(上)[？？？？？]
# 			ENDIF
# 		ENDIF
# 		IF 表示部位:LOCAL == "下半身下着1" && EQUIP:C_ID:下半身下着２ == 0 && EQUIP:C_ID:下半身下着1 == 0 && EQUIP:C_ID:ボディースーツ == 0 && EQUIP:C_ID:レオタード == 0 && EQUIP:C_ID:0
# 			IF !上半身下着表示(C_ID) && !下半身下着表示(C_ID)
# 				PRINTFORML 　装備:下着　　[？？？？？]
# 				CONTINUE
# 			ELSEIF !下半身下着表示(C_ID)
# 				PRINTFORML 　装備:下着(下)[？？？？？]
# 			ELSE
# 				STR:(12000 + LOCAL) = はいてない
# 				PRINTFORML 　装備:下着(下)[はいてない]
# 			ENDIF
# 		ENDIF
		
# 		SIF !EQUIP:C_ID:装備部位 
# 			CONTINUE
# 		IF STRLENS(CSTR:C_ID:(50 + 装備部位)) && !CFLAG:C_ID:パジャマ
# 			表示内容 '= CSTR:C_ID:(50 + 装備部位)
# 		;パンツは専用処理が必要
# 		ELSEIF 表示部位:LOCAL == "上半身下着1" && !(C_ID == MASTER) && !上半身下着表示(C_ID)
# 			SIF !下半身下着表示(C_ID)
# 				CONTINUE
# 			表示内容 '= "？？？？？"
# 		ELSEIF 表示部位:LOCAL == "下半身下着２" && !(C_ID == MASTER) && !下半身下着表示(C_ID)
# 			IF !上半身下着表示(C_ID)
# 				PRINTFORML 　装備:下着　　[？？？？？]
# 				CONTINUE
# 			ELSE
# 				表示内容 '= "？？？？？"
# 			ENDIF
# 		ELSE
# 			IF 表示部位:LOCAL == "上半身下着1"
# 				表示内容 '= BRANAME(EQUIP:C_ID:上半身下着1, C_ID)
# 			ELSEIF 表示部位:LOCAL == "下半身下着２"
# 				表示内容 '= PANTSNAME(EQUIP:C_ID:下半身下着２, C_ID)
# 			ELSE
# 				表示内容 '= CLOTHNAME(装備部位, EQUIP:C_ID:装備部位)
# 			ENDIF
# 			STR:(12000 + LOCAL) = %表示内容%
# 		ENDIF
# 		PRINTFORML %表示ラベル:LOCAL%[%表示内容%]
# 	NEXT
