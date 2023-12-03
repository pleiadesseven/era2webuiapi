import pandas as pd
import os
import random
from eraImascgpro.emo import Expression
import re
from sub import get_df
from sub import get_df_2key
from sub import get_width_and_height
from sub import chikan
from sub import find_csv_path
from sub import csvlist

# order自体を変化させる前処理
# たとえば
# 条件によりコマンド差し替え（乳サイズでパイズリ→ナイズリ
# キャラ差し替え　EXフラグが立っていたらEXキャラ用の名前に変更する
# など
def preceding(order):
    Nパイズリ = "82"
    Nナイズリ = "701" #存在しないコマンド番号。
    N胸愛撫 = "6"
    N着衣胸愛撫 = "702" #存在しないコマンド番号。

    comNo = str(order["コマンド"])

    # 巨乳未満のキャラのパイズリはナイズリに変更
    # (ちんちんが隠れてしまうような描写は普乳を逸脱しているため)
    if not (("巨乳" in order["talent"]) or ("爆乳" in order["talent"])):
        if comNo == Nパイズリ:
            comNo = Nナイズリ

    # 着衣時の胸愛撫はCHAKUMOMIのLoraを適用
    # キャラLoraと相性よくないみたいでつらい
    if order["上半身着衣状況"] != 0:
        if comNo == N胸愛撫:
            comNo = N着衣胸愛撫


    order["コマンド"] = comNo

    return order


# orderをもとにプロンプトを整形する関数
def promptmaker(order):
    
    # orderを変化させる事前処理 コマンドが変われば解像度の変化もありえる
    order = preceding(order)

    kaizoudo = ""
    gen_width = 0
    gen_height = 0

    prompt = ""
    negative = ""

    flags = {"drawchara":0,"drawface":0,"drawbreasts":0,"drawvagina":0,"drawanus":0}

    # Effect.csvとEvent.csvを読みこんでおく
    csvname, csvfile_path= find_csv_path(csvlist, 'Effect.csv')
    csv_efc = pd.read_csv(filepath_or_buffer=csvfile_path)

    csvname, csvfile_path= find_csv_path(csvlist, 'Event.csv')
    csv_eve = pd.read_csv(filepath_or_buffer=csvfile_path)

    prompt += get_df(csvname, csv_efc,'名称','基礎プロンプト','プロンプト') + ","
    negative += get_df(csvname, csv_efc,'名称','基礎プロンプト','ネガティブ')  + ","

    #シーン分岐

    #場所とキャラを描写する
    if order["scene"] == "ターゲット切替" or order["scene"] == "マスター移動":
        if order["キャラ固有番号"] == 0:
            # targetがいないとき
            prompt += "(empty scene),"
            negative += "(1girl:1.5),"
        else:
            # 立ち絵表示　背景描写を強化
            prompt += "1girl standing, detailed scenery in the background,"
            flags["drawchara"] = 1
            flags["drawface"] = 1
            
        #ロケーション
        p,n = get_location(order)
        prompt += p
        negative += n


    #ここからTRAIN コマンド実行時の絵
    if order["scene"] == "TRAIN":
        #コマンドの処理 Train.csvを読む
        csvname, csvfile_path= find_csv_path(csvlist, 'Train.csv')
        csv_tra = pd.read_csv(filepath_or_buffer=csvfile_path)

        # TRAINNAME関数はないと思い込んでいたので番号で処理している
        comNo = str(order["コマンド"])

        # 体位から読み取ったキャラ描画、顔描画、胸描画のフラグ（0か1が入る)
        flags["drawchara"] =  get_df(csvname, csv_tra,"コマンド番号",comNo,"キャラ描画")
        flags["drawface"] =  get_df(csvname, csv_tra,"コマンド番号",comNo,"顔描画")
        flags["drawbreasts"] =  get_df(csvname, csv_tra,"コマンド番号",comNo,"胸描画")
        flags["drawvagina"] = get_df(csvname, csv_tra,"コマンド番号",comNo,"ヴァギナ描画")
        flags["drawanus"] = get_df(csvname, csv_tra,"コマンド番号",comNo,"アナル描画")
        
        # コマンドが未記入の場合はEvent.csvの汎用調教を呼ぶ
        pro = get_df(csvname, csv_tra,"コマンド番号",comNo,"プロンプト")
        if pro == "":
            prompt += get_df(csvname, csv_eve,"名称","汎用調教","プロンプト")
            prompt += ","
            negative += get_df(csvname, csv_eve,"名称","汎用調教","ネガティブ")  
            negative += ","

            flags["drawchara"] = get_df(csvname, csv_eve,"名称","汎用調教","キャラ描画")
            flags["drawface"] = get_df(csvname, csv_eve,"名称","汎用調教","顔描画")
            flags["drawbreasts"] = get_df(csvname, csv_eve,"名称","汎用調教","胸描画")
            flags["drawvagina"] = get_df(csvname, csv_eve,"名称","汎用調教","ヴァギナ描画")
            flags["drawanus"] = get_df(csvname, csv_eve,"名称","汎用調教","アナル描画")

        else:
            # cgpro コマンド成否で分岐はめんどいので実装しない
            # 現状だとソース変動があるときにしか画像表示関数は呼ばれない
            order["success"] = 1 # 必ず成功

            deny = get_df(csvname, csv_tra,"コマンド番号",comNo,"拒否プロンプト")
            if deny == "":
                #拒否プロンプトが空なら成否判定なしと判断、通常プロンプトを出力する
                chk_success = True
            elif order["success"] == 1:
                #判定に成功した
                chk_success = True
            else:
                #判定に失敗した。拒否プロンプトを出力する
                chk_success = False

            if chk_success:
                prompt += pro
                prompt += ","
                negative += get_df(csvname, csv_tra,"コマンド番号",comNo,"ネガティブ")
                negative += ","
            else:
                prompt += deny
                prompt += ","
                negative += get_df(csvname, csv_tra,"コマンド番号",comNo,"拒否ネガティブ")
                negative += ","

        # 付着した精液
        # prompt += stain(order,flags)
        #装備 調教対象キャラが映るときのみ
        if flags["drawchara"] == 1:
            p,n = equipment(order,flags)
            prompt += p
            negative += n
        #ロケーション
        p,n = get_location(order)
        prompt += p
        negative += n

        #解像度
        kaizoudo = get_kaizoudo(order)


    #キャラ描写
    if flags["drawchara"] == 1:

        # キャラ描写の前にBREAKしておく？これいいのか悪いのかわからぬ
        # prompt += "BREAK,"

        # キャラ描写の前に衣服
        p,n = clothing(order,flags)
        prompt += p
        negative += n

        # キャラ描写で毎回記述するプロンプト Effect.csvから読み出す
        prompt += get_df(csvname, csv_efc,"名称","人物プロンプト","プロンプト") + ","

        # Character.csvとAdd_character.csvを結合
        csvname, csvfile_path= find_csv_path(csvlist, 'Character.csv')
        csv_cha = pd.read_csv(filepath_or_buffer=csvfile_path)
        csvname, csvfile_path= find_csv_path(csvlist, 'Add_Character.csv')
        add_cha = pd.read_csv(filepath_or_buffer=csvfile_path)

        csv_cha = pd.concat([csv_cha,add_cha])

        # 特別な名前でプロンプトを登録してある場合、キャラ描写を強制的に上書きする処理
        uwagaki = get_df(csvname, csv_cha,"キャラ名","描画キャラ上書き","プロンプト")
        if uwagaki != "": #空欄じゃなかったら上書き
            prompt += "\(" + uwagaki + "\),"
            negative += get_df(csv_cha,"キャラ名","描画キャラ上書き","ネガティブ") + ","
        else:
            #割り込みがなければ通常のキャラプロンプト読み込み処理
            chaName = order["target"]
            prompt += "\(" + get_df(csvname, csv_cha,"キャラ名",chaName,"プロンプト") + ":" + str(get_df(csvname, csv_cha,"キャラ名",chaName,"プロンプト強調")) + "\),"
            prompt += "\(" + get_df(csvname, csv_cha,"キャラ名",chaName,"プロンプト2") + "\),"
            prompt += get_df(csvname, csv_cha,"キャラ名",chaName,"キャラLora") + ","
            negative += get_df(csvname, csv_cha,"キャラ名",chaName,"ネガティブ") +  ","



        # エフェクト等 TFLAGは調教終了時には初期化されない。TRAINに限定しないと料理中に射精とかが起こる
        if order["scene"] == "TRAIN":
            #射精
            prompt += cumshot(order)
        
            # ヴァギナ描画onのとき
            if flags["drawvagina"] == 1:
                # 潤滑によるpussy juice
                if order["palam"]["潤滑"] < 200:
                    negative += "pussy juice,"
                elif order["palam"]["潤滑"] in range(1000,2500):
                    prompt += "pussy juice,"
                elif order["palam"]["潤滑"] in range(2500,5000):
                    prompt += "dripping pussy juice,"
                else:
                    prompt += "(dripping pussy juice),"
                # 破瓜の血       
                # if order["処女喪失"] > 0:
                    # prompt += get_df(csvname, csv_efc,"名称","処女喪失","プロンプト") + ","
                # if order["今回の調教で処女喪失"] > 0:
                    # prompt += get_df(csvname, csv_efc,"名称","今回の調教で処女喪失","プロンプト") + ","            
                if order["放尿"] > 0:
                        prompt += get_df(csvname, csv_efc,"名称","放尿","プロンプト") + ","
            if flags["drawbreasts"]:
                if order["噴乳"] > 0:
                    prompt += get_df(csvname, csv_efc,"名称","噴乳","プロンプト") + ","
            # ここまでTRAIN限定のエフェクト
        
        if "妊娠" in order["talent"]:
            # 標準で20日で出産する。残14日から描写し、残8日でさらに進行
            if (order["出産日"] - order["日付"]) in range(8,14):
                prompt += get_df(csvname, csv_efc,"名称","妊娠中期","プロンプト") + ","
            elif (order["出産日"] - order["日付"]) <= 8:
                prompt += get_df(csvname, csv_efc,"名称","妊娠後期","プロンプト") + ","

        #乳サイズ、体型の関数を呼び出す
        p,n = body_shape(order,flags)
        prompt += p
        negative += n

        #髪色の関数 ※3000番台の名無しキャラ、および息子(2048)と娘(2049)のみ
        # if (order["キャラ固有番号"] in range(3000,4000)) or (order["キャラ固有番号"] in (2048,2049)):
        #     prompt += haircolor(order)

        #髪型の関数
        # p,n = hairstyle(order)
        # prompt += p
        # negative += n        

        #目の色をorderに追記しておく(Expression関数でclosed eyesの判定をした後に反映する)
        order["eyecolor"] = get_df(csvname, csv_cha,"キャラ名",order["target"],"目の色")

        #表情ブレンダー
        p,n = Expression(order,flags)
        prompt += p
        negative += n
    #ここまでキャラ描画フラグがonのときの処理



    # 昼夜の表現
        # やたらと夜景や黄昏時を出したがるので強めにネガ
        # 屋外なら青空とかを書きたいが分岐が面倒くさい
        if order["時間"] in range(0,360):
            prompt += "at night,"
            negative += "(blue sky,twilight:1.3),"
        elif order["時間"] in range(360,720):
            prompt += "day,"
            negative += "(night sky,night scene,twilight:1.3),"
        elif order["時間"] in range(720,1060):
            prompt += "day,"
            negative += "(night sky,night scene,twilight:1.3),"
        elif order["時間"] in range(1060,1150):
            prompt += "in the twilight,"
            negative += "(blue sky:1.3),"
        elif order["時間"] >= 1150:
            prompt += "at night,"
            negative += "(blue sky,twilight:1.3),"


    # 置換機能の関数を呼ぶ
    # プロンプト中に%で囲まれた文字列があれば置換する機能
    # 失敗するとErrorというプロンプトが残る
    ReplaceList= os.path.join(os.path.dirname(__file__), 'csvfiles\\ReplaceList.csv')
    prompt = chikan(prompt,ReplaceList)
    negative = chikan(negative,ReplaceList)
    
    # 解像度文字列を解釈する関数
    gen_width,gen_height = get_width_and_height(kaizoudo,ReplaceList)

    # 重複カンマを1つにまとめる
    prompt = re.sub(',+',',',prompt)
    negative = re.sub(',+',',',negative)

    return prompt,negative,gen_width,gen_height
# *********************************************************************************************************
# ----------ここまでpromptmaker----------------------------------------------------------------------------------
# *********************************************************************************************************


# 体型素質
# 一致する素質を持っていればTalent.csvに書かれたプロンプトを記入
def body_shape (order,flags):
    prompt = ""
    negative = ""
    csvname, csvfile_path= find_csv_path(csvlist, 'Talent.csv')
    csv_tal = pd.read_csv(filepath_or_buffer=csvfile_path)


    # 乳サイズ
    # 乳強調すると脱ぎたがるのどうしよう
    if flags["drawbreasts"] == 1:
        talents = ["絶壁","貧乳","巨乳","爆乳"]
        for tal in talents:
            if tal in order["talent"]:
                prompt += get_df(csv_tal,"名称",tal,"プロンプト") + ","
                negative += get_df(csv_tal,"名称",tal,"ネガティブ") + ","

    # 体格、体型
    talents = ["小人体型","巨躯","小柄体型","ぽっちゃり","ムチムチ","スレンダー","がりがり"]
    for tal in talents:
        if tal in order["talent"]:
            prompt += get_df(csv_tal,"名称",tal,"プロンプト") + ","
            negative += get_df(csv_tal,"名称",tal,"ネガティブ") + ","

    # 胸愛撫など、普通乳なのに巨乳に描かれがちなコマンドのときプロンプトにsmall breastsを付加する
    chk_list = ["爆乳","巨乳","貧乳","絶壁"]
    and_list = set(order['talent']) & set(chk_list)
    # リストに一致しないとき即ち普通乳のとき
    if (len(and_list)) == 0:
        # 胸愛撫、ぱふぱふ、後背位胸愛撫
        if str(order["コマンド"]) in ("6","606","702"):
            prompt += "small breasts,"


    return prompt,negative

# 髪色
# def haircolor(order):
#     csvname, csvfile_path= find_csv_path(csvlist, 'Talent.csv')
#     csv_tal = pd.read_csv(filepath_or_buffer=csvfile_path)
#     prompt = ""
#     negative = ""
#     talents = ["黒髪","栗毛","金髪","赤毛","銀髪","青髪","緑髪","ピンク髪","紫髪","白髪","オレンジ髪","水色髪","灰髪"]
#     for tal in talents:
#         if tal in order["talent"]:
#             # csvには色だけ書いてるのでhairをつける
#             prompt += get_df(csv_tal,"名称",tal,"プロンプト") + " hair,"
#             negative += get_df(csv_tal,"名称",tal,"ネガティブ") + " hair,"
#     return prompt


# 髪型 
def hairstyle(order):
    csvname, csvfile_path= find_csv_path(csvlist, 'Talent.csv')
    csv_tal = pd.read_csv(filepath_or_buffer=csvfile_path)
    prompt = ""
    negative = ""
    talents = ["長髪","セミロング","ショートカット","ポニーテール","ツインテール","サイドテール","縦ロール","ツインリング","三つ編み","短髪","おさげ髪","ポンパドール","ポニーアップ","サイドダウン","お団子髪","ツーサイドアップ","ダブルポニー","横ロール","まとめ髪","ボブカット","シニヨン","ロングヘア"]
    for tal in talents:
        if tal in order["talent"]:
            prompt += get_df(csv_tal,"名称",tal,"プロンプト") + ","
            negative += get_df(csv_tal,"名称",tal,"ネガティブ") + ","
    return prompt,negative

# 一時装備､SEXTOYなど
# CSVを2列で検索する
def equipment(order,flags):
    prompt = ""
    negative = ""
    csvname, csvfile_path= find_csv_path(csvlist, 'Equip.csv')
    csv_equ = pd.read_csv(filepath_or_buffer=csvfile_path)

    N膣装備 = ["11","12","13","22"]
    Nアナル装備 = ["14","15","23"]    
    # 存在するすべてのequipについて繰り返す
    for key,value in order["equip"].items():
        # 構図による装備品のスキップ
        if key in N膣装備:
            print("v")
            print(flags["drawvagina"])
            if flags["drawvagina"] == 0:
                continue
        if key in Nアナル装備:
            print("a")
            print(flags["drawanus"])
            if flags["drawanus"] == 0:
                continue
        
        equ = get_df_2key(csvname, csv_equ,"TEQUIP",int(key),"値",int(value),"プロンプト")
        if  equ != "ERROR":
            prompt += equ + ","
        equ = get_df_2key(csvname, csv_equ,"TEQUIP",int(key),"値",int(value),"ネガティブ")
        if  equ != "ERROR":
            negative += equ + ","
        
    return prompt,negative

#ロケーション
#Strで定義されている番号が汚えせめてcsvはみやすくする
#
def get_location(order):
    prompt = ""
    negative = ""

    # 700箇所
    csvname, csvfile_path= find_csv_path(csvlist, 'Location.csv')
    csv_loc = pd.read_csv(filepath_or_buffer=csvfile_path)
    
    prompt += get_df(csvname, csv_loc,"地名",order["現在位置"],"プロンプト")
    prompt += ","
    negative += get_df(csvname, csv_loc,"地名",order["現在位置"],"ネガティブ")
    negative += ","

    return prompt, negative

# 射精
def cumshot(order):
    射精箇所 = order["射精箇所"]
    prompt = ""
    #ビット　1=膣内 2=アナル 3=手淫 4=口淫 5=パイズリ 6=素股 7=足コキ 8=体表 9=アナル奉仕

    if 射精箇所 & 1 != 0:
        prompt += "(cum in pussy,internal ejaculation),"    
    if 射精箇所 & 2 != 0:
        prompt += "(cum in ass),"
    if 射精箇所 & 4 != 0:
        prompt += "(cum on hand, ejaculation, projectile cum),"
    if 射精箇所 & 8 != 0:
        prompt += "(cum in mouth),"
    if 射精箇所 & 16 != 0:
        prompt += "(cum on breasts, ejaculation, projectile cum),"
    if 射精箇所 & 32 != 0:
        prompt += "(cum on lower body, ejaculation, projectile cum),"
    if 射精箇所 & 64 != 0:
        prompt += "(cum on feet, ejaculation, projectile cum),"
    if 射精箇所 & 128 != 0:
        prompt += "(cum on stomach, ejaculation, projectile cum),"
    if 射精箇所 & 256 != 0:
        prompt += "(ejaculation, projectile cum),"
    #射精エフェクト
    if 射精箇所 != 0:
        csvname, csvfile_path= find_csv_path(csvlist, 'Effect.csv')
        csv_efc = pd.read_csv(filepath_or_buffer=csvfile_path)

        if order["MASTER射精量"] <= 1:
            prompt += get_df(csvname, csv_efc,"名称","主人が射精","プロンプト") + ","
        else:
            prompt += get_df(csvname, csv_efc,"名称","主人が大量射精","プロンプト") + ","

    return prompt

#汚れ
def stain(order,flags):
    prompt = ""
    # if ((order["髪の汚れ"] & 4)  == 4):
    #     prompt += "(facial,bukkake:1.2),"
    if flags["drawbreasts"] == 1:
        if (order["胸の汚れ"] & 4)  == 4:
            prompt += "(cum on breasts),"
    if flags["drawvagina"] == 1:
        if (order["膣内射精フラグ"]) >= 1:
            prompt += "cum drip from pussy,"
    return prompt
# cum on ～ はちんちんを誘発、semen on ～ はほとんど効果がない
# milkはときどきグラスが出る


# 解像度をcsvから読む
# シーン分岐ごとに読む
def get_kaizoudo(order):
    # TRAINとその他のEVENTで読み取るcsvが異なる
    if order["scene"] == "TRAIN":
        csvname, csvfile_path= find_csv_path(csvlist, 'Train.csv')
        csvfile = pd.read_csv(filepath_or_buffer=csvfile_path)
        kaizoudo = str(get_df(csvname,csvfile,"コマンド番号",str(order["コマンド"]),"解像度"))
    else:
        csvname, csvfile_path= find_csv_path(csvlist, 'Event.csv')
        csvfile = pd.read_csv(filepath_or_buffer=csvfile_path)
        kaizoudo = str(get_df(csvname,csvfile,"名称",str(order["scene"]),"解像度"))
    
    return kaizoudo

# 服装
def clothing(order,flags):
    prompt = ""
    negative = ""
    csvname, csvfile_path= find_csv_path(csvlist, 'Cloth.csv')
    csv_clo = pd.read_csv(filepath_or_buffer=csvfile_path)
    # 脱衣コマンドのコマンド番号
    N上半身脱衣_上着 = "200"
    N下半身脱衣_上着 = "201"
    N上半身脱衣_下着 = "202"
    N下半身脱衣_下着 = "203"
    # 体から離れた衣服の生成打率はいまだ著しく低いので、脱いでいる服の描写は未実装。脱衣コマンドを実行すると脱衣後の姿を表示する。
    # 決して諦めてはならない。

    ブラ露出フラグ = 0
    パンツ露出フラグ = 0
    乳露出フラグ = 0
    秘部露出フラグ = 0
    上半身はだけフラグ = 0 #未実装 上着着衣のまま乳を見せるコマンド用
    下半身はだけフラグ = 0 #スカート着衣のまま中身を見せるコマンド用

    # 下半身はだけ　クンニ、秘貝開帳、自慰、ローター、Eマッサージャ、クリキャップ、バイブ、アナルバイブ、アナルビーズ、正常位、後背位、正常位アナル、後背位アナル、逆レイプ、騎乗位、騎乗位アナル、対面座位、背面座位、対面座位アナル、背面座位アナル、二穴挿し、素股、スパンキング、
    if order["コマンド"] in ["1","8","9","40","41","42","44","45","46","60","61","62","63","64","65","66","67","68","69","70","71","72","83","100"]:
        下半身はだけフラグ = 1

    # 下着１（貞操帯、絆創膏、ニプレス）は未実装


    # ブラ露出判定
    # 上着が0枚 or 上着1枚かつ脱衣中 に露出フラグが立つ。ノーブラの判定はあとでやる
    if 上半身上着重ね着数(order) == 0 or (上半身上着重ね着数(order) == 1 and order["コマンド"] == N上半身脱衣_上着):
        ブラ露出フラグ = 1
    elif 上半身はだけフラグ == 1:
        ブラ露出フラグ = 1
    
    # パンツ露出判定　ブラと同様
    if 下半身上着重ね着数(order) == 0 or (下半身上着重ね着数(order) == 1 and order["コマンド"] == N下半身脱衣_上着):
        パンツ露出フラグ = 1 
    elif 下半身はだけフラグ == 1:
        パンツ露出フラグ = 1
    
    # 乳露出判定
    # 着てない or ブラのみの状態から脱ぐ、または元々ノーブラの状態でブラが見える条件を満たす
    if order["上半身着衣状況"] == 0 or (上半身上着重ね着数(order) == 0 and order["コマンド"] == N上半身脱衣_下着) or (order["上半身下着２"] == 0 and ブラ露出フラグ == 1):
        ブラ露出フラグ = 0
        乳露出フラグ = 1

    # 秘部露出判定
    # なにも履いてない or パンツだけ履いてるのを脱ぐ、または元々ノーパンの状態でパンツが見える条件を満たす
    if order["下半身着衣状況"] == 0 or (下半身上着重ね着数(order) == 0 and order["コマンド"] == N下半身脱衣_下着) or (order["下半身下着２"] == 0 and パンツ露出フラグ == 1):
        パンツ露出フラグ = 0 
        秘部露出フラグ = 1
    
    # 裸体描写
    # 上半身だけ着てる
    if 秘部露出フラグ == 1 and 乳露出フラグ == 0:
        prompt += "nsfw, her lower body is naked,(bottomless, naked clotch, pussy),"
    # 下半身だけ着てる
    if 秘部露出フラグ == 0 and 乳露出フラグ == 1:
        prompt += "nsfw, her upper body is naked,(topless, naked breasts, nipples),"
    # 全裸
    if 秘部露出フラグ == 1 and 乳露出フラグ == 1:
        prompt += "nsfw, full nude,completely naked, (naked breasts,nipples),"

    # 上着描写
    # 上半身上着
    if (ブラ露出フラグ == 0 and 乳露出フラグ == 0) or 上半身はだけフラグ == 1:
        clothings = ["上半身上着１","上半身上着２","ボディースーツ","ワンピース","着物","レオタード"]
        for clo in clothings:
            clothName= str(order[clo])
            if order[clo] != 0:
                prompt += "(wearing " + " " + get_df(csvname, csv_clo,"衣類名",clothName,"プロンプト") + ":1.3),"
                negative += get_df(csvname, csv_clo,"衣類名",clothName,"ネガティブ") + ","

    # 下半身上着
    if (パンツ露出フラグ == 0 and 秘部露出フラグ == 0) or 下半身はだけフラグ == 1:
        clothings = ["下半身上着１","下半身上着２","スカート"]
        for clo in clothings:
            clothName = str(order[clo])
            if order[clo] != 0:
                prompt += "(wearing " + " " + get_df(csvname, csv_clo,"衣類名",clothName,"プロンプト") + ":1.3),"
                negative += get_df(csvname, csv_clo,"衣類名",clothName,"ネガティブ") + ","


    if ブラ露出フラグ == 1:
        if order["上半身下着２"] != 0:
            prompt += "(wearing " + " " + get_df(csvname, csv_clo,"衣類名",str(order["上半身下着２"]),"プロンプト") + ":1.3),"

    if パンツ露出フラグ == 1:
        if order["下半身下着２"] != 0:
            # パンツの種類は未対応
            prompt += "(wearing " + " panties:1.3),"

    # panty aside
    # 挿入とクンニ
    if (order["マスターがＶ挿入"] != 0 )or(order["マスターがＡ挿入"] != 0) or (order["コマンド"] == "1"):
        if order["下半身下着２"] != 0:
            prompt += "(naked pussy, pantie aside),"

    return prompt,negative


def 上半身上着重ね着数(order):
    return ((order["上半身上着１"] != 0) + (order["上半身上着２"] != 0) + (order["ボディースーツ"] != 0) + (order["ワンピース"] != 0) + (order["着物"] != 0) + (order["レオタード"] != 0))

def 下半身上着重ね着数(order):
    return ((order["下半身上着１"] != 0) + (order["下半身上着２"] != 0) + (order["スカート"] != 0) + (order["ボディースーツ"] != 0) + (order["ワンピース"] + order["着物"] != 0) + (order["レオタード"] != 0))