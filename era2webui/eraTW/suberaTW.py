import pandas as pd
from eraTW.emo import Expression
import re
from module.sub import get_width_and_height

from module.csv_manager import CSVMFactory
csvm = CSVMFactory.get_instance()
from eraTW.existobj import ObjExistenceManager, get_str


# order自体を変化させる前処理
# たとえば
# 条件によりコマンド差し替え（乳サイズでパイズリ→ナイズリ
# キャラ差し替え　EXフラグが立っていたらEXキャラ用の名前に変更する
# など

def preceding(sjh):
    #SaveJSONHandlerにしまわれたJSONの値は int
    Nパイズリ = 82
    Nナイズリ = 701 #存在しないコマンド番号。
    N胸愛撫 = 6
    N着衣胸愛撫 = 702 #存在しないコマンド番号。


    comNo = sjh.get_save("コマンド")

    # 巨乳未満のキャラのパイズリはナイズリに変更
    # (ちんちんが隠れてしまうような描写は普乳を逸脱しているため)
    if not (("巨乳" in sjh.get_save("talent")) or ("爆乳" in sjh.get_save("talent"))):
        if comNo == Nパイズリ:
            comNo = Nナイズリ

    # 着衣時の胸愛撫はCHAKUMOMIのLoraを適用
    # キャラLoraと相性よくないみたいでつらい
    if sjh.get_save("上半身着衣状況") != 0:
        if comNo == N胸愛撫:
            comNo = N着衣胸愛撫


    # 既存のデータを取得
    current_data = sjh.data
    # 特定のキーの値を更新
    current_data["コマンド"] = comNo
    # 更新されたデータで data 属性を更新
    sjh.update_data(current_data)
    return sjh


# orderをもとにプロンプトを整形する関数
def promptmaker(sjh):  
    # SaveJSONHandler の class dict の更新 コマンドが変われば解像度の変化もありえる
    sjh = preceding(sjh)
    
    kaizoudo = ""
    gen_width = 0
    gen_height = 0

    prompt = ""
    negative = ""

    flags = {"drawchara":0,"drawface":0,"drawbreasts":0,"drawvagina":0,"drawanus":0}

    # Effect.csvとEvent.csvは起動時に読み込んだ
    csv_efc = 'Effect.csv'
    csv_eve = 'Event.csv'

    prompt += csvm.get_df(csv_efc,'名称','基礎プロンプト','プロンプト') + ","
    negative += csvm.get_df(csv_efc,'名称','基礎プロンプト','ネガティブ')  + ","

    #シーン分岐

    #場所とキャラを描写する
    if sjh.get_save("scene") == "ターゲット切替" or sjh.get_save("scene") == "マスター移動":
        if sjh.get_save("キャラ固有番号") == 0:
            # targetがいないとき
            prompt += "(empty scene),"
            negative += "(1girl:1.5),"
        else:
            # 立ち絵表示　背景描写を強化
            prompt += "1girl standing, detailed scenery in the background,"
            flags["drawchara"] = 1
            flags["drawface"] = 1
            
        #ロケーション
        p,n = get_location(sjh)
        prompt += p
        negative += n


    #ここからTRAIN コマンド実行時の絵
    if sjh.get_save("scene") == "TRAIN":
        csv_tra = 'Train.csv'

        # TRAINNAME関数はないと思い込んでいたので番号で処理している
        comNo = sjh.get_save("コマンド")

        # 体位から読み取ったキャラ描画、顔描画、胸描画のフラグ（0か1が入る)
        flags["drawchara"] =  csvm.get_df(csv_tra,"コマンド番号",comNo,"キャラ描画")
        flags["drawface"] =  csvm.get_df(csv_tra,"コマンド番号",comNo,"顔描画")
        flags["drawbreasts"] =  csvm.get_df(csv_tra,"コマンド番号",comNo,"胸描画")
        flags["drawvagina"] = csvm.get_df(csv_tra,"コマンド番号",comNo,"ヴァギナ描画")
        flags["drawanus"] = csvm.get_df(csv_tra,"コマンド番号",comNo,"アナル描画")
        
        # コマンドが未記入の場合はEvent.csvの汎用調教を呼ぶ
        pro = csvm.get_df(csv_tra,"コマンド番号",comNo,"プロンプト")
        if pro == "":
            prompt += csvm.get_df(csv_eve,"名称","汎用調教","プロンプト")
            prompt += ","
            negative += csvm.get_df(csv_eve,"名称","汎用調教","ネガティブ")  
            negative += ","

            flags["drawchara"] = csvm.get_df(csv_eve,"名称","汎用調教","キャラ描画")
            flags["drawface"] = csvm.get_df(csv_eve,"名称","汎用調教","顔描画")
            flags["drawbreasts"] = csvm.get_df(csv_eve,"名称","汎用調教","胸描画")
            flags["drawvagina"] = csvm.get_df(csv_eve,"名称","汎用調教","ヴァギナ描画")
            flags["drawanus"] = csvm.get_df(csv_eve,"名称","汎用調教","アナル描画")

        else:
            # # cgpro コマンド成否で分岐はめんどいので実装しない
            # # 現状だとソース変動があるときにしか画像表示関数は呼ばれない
            #機能してないのであとで直す
            # sjh.get_save("success") == 1 # 必ず成功

            deny = csvm.get_df(csv_tra,"コマンド番号",comNo,"拒否プロンプト")
            if deny == "":
                #拒否プロンプトが空なら成否判定なしと判断、通常プロンプトを出力する
                chk_success = True
            elif sjh.get_save("success") == 1:
                #判定に成功した
                chk_success = True
            else:
                #判定に失敗した。拒否プロンプトを出力する
                chk_success = False

            if chk_success:
                prompt += pro
                prompt += ","
                negative += csvm.get_df(csv_tra,"コマンド番号",comNo,"ネガティブ")
                negative += ","
            else:
                prompt += deny
                prompt += ","
                negative += csvm.get_df(csv_tra,"コマンド番号",comNo,"拒否ネガティブ")
                negative += ","

        # 付着した精液
        # prompt += stain(sjh,flags)
        #装備 調教対象キャラが映るときのみ
        if flags["drawchara"] == 1:
            p,n = equipment(sjh,flags)
            prompt += p
            negative += n
        #ロケーション
        p,n = get_location(sjh)
        prompt += p
        negative += n

        #解像度
        kaizoudo = get_kaizoudo(sjh)


    #キャラ描写
    if flags["drawchara"] == 1:

        # キャラ描写の前にBREAKしておく？これいいのか悪いのかわからぬ
        # prompt += "BREAK,"

        # キャラ描写の前に衣服
        p,n = clothing(sjh,flags)
        prompt += p
        negative += n

        # キャラ描写で毎回記述するプロンプト Effect.csvから読み出す
        prompt += csvm.get_df(csv_efc,"名称","人物プロンプト","プロンプト") + ","

        csv_cha = 'Character.csv'

        # 特別な名前でプロンプトを登録してある場合、キャラ描写を強制的に上書きする処理
        uwagaki = csvm.get_df(csv_cha,"キャラ名","描画キャラ上書き","プロンプト")
        if uwagaki != "": #空欄じゃなかったら上書き
            prompt += "\(" + uwagaki + "\),"
            negative += csvm.get_df(csv_cha,"キャラ名","描画キャラ上書き","ネガティブ") + ","
        else:
            #割り込みがなければ通常のキャラプロンプト読み込み処理
            chaName = sjh.get_save("target")
            prompt += "\(" + csvm.get_df(csv_cha,"キャラ名",chaName,"プロンプト") + ":" + str(csvm.get_df(csv_cha,"キャラ名",chaName,"プロンプト強調")) + "\),"
            prompt += "\(" + csvm.get_df(csv_cha,"キャラ名",chaName,"プロンプト2") + "\),"
            prompt += csvm.get_df(csv_cha,"キャラ名",chaName,"キャラLora") + ","
            negative += csvm.get_df(csv_cha,"キャラ名",chaName,"ネガティブ") +  ","



        # エフェクト等 TFLAGは調教終了時には初期化されない。TRAINに限定しないと料理中に射精とかが起こる
        if sjh.get_save("scene") == "TRAIN":
            #射精
            prompt += cumshot(sjh)
        
            # ヴァギナ描画onのとき
            if flags["drawvagina"] == 1:
                # 潤滑によるpussy juice
                if sjh.get_save("palam")["潤滑"] < 200:
                    negative += "pussy juice,"
                elif sjh.get_save("palam")["潤滑"] in range(1000,2500):
                    prompt += "pussy juice,"
                elif sjh.get_save("palam")["潤滑"] in range(2500,5000):
                    prompt += "dripping pussy juice,"
                else:
                    prompt += "(dripping pussy juice),"
                # 破瓜の血       
                # if sjh.get_save("処女喪失"] > 0:
                    # prompt += csvm.get_df(csv_efc,"名称","処女喪失","プロンプト") + ","
                # if sjh.get_save("今回の調教で処女喪失"] > 0:
                    # prompt += csvm.get_df(csv_efc,"名称","今回の調教で処女喪失","プロンプト") + ","            
                if sjh.get_save("放尿") > 0:
                        prompt += csvm.get_df(csv_efc,"名称","放尿","プロンプト") + ","
            if flags["drawbreasts"]:
                if sjh.get_save("噴乳") > 0:
                    prompt += csvm.get_df(csv_efc,"名称","噴乳","プロンプト") + ","
            # ここまでTRAIN限定のエフェクト
        
        if "妊娠" in sjh.get_save("talent"):
            # 標準で20日で出産する。残14日から描写し、残8日でさらに進行
            if (sjh.get_save("出産日") - sjh.get_save("日付")) in range(8,14):
                prompt += csvm.get_df(csv_efc,"名称","妊娠中期","プロンプト") + ","
            elif (sjh.get_save("出産日") - sjh.get_save("日付")) <= 8:
                prompt += csvm.get_df(csv_efc,"名称","妊娠後期","プロンプト") + ","

        #乳サイズ、体型の関数を呼び出す
        p,n = body_shape(sjh,flags)
        prompt += p
        negative += n

        #髪色の関数 ※3000番台の名無しキャラ、および息子(2048)と娘(2049)のみ
        # if (sjh.get_save("キャラ固有番号") in range(3000,4000)) or (sjh.get_save("キャラ固有番号") in (2048,2049)):
        #     prompt += haircolor(sjh)

        #髪型の関数
        # p,n = hairstyle(sjh)
        # prompt += p
        # negative += n        

        #目の色をorderに追記しておく(Expression関数でclosed eyesの判定をした後に反映する)
        sjh.get_save("eyecolor") == csvm.get_df(csv_cha,"キャラ名",sjh.get_save("target"),"目の色")

        #表情ブレンダー
        p,n = Expression(sjh,flags)
        prompt += p
        negative += n
    #ここまでキャラ描画フラグがonのときの処理


    # 昼夜の表現
        # やたらと夜景や黄昏時を出したがるので強めにネガ
        # 屋外なら青空とかを書きたいが分岐が面倒くさい
        if sjh.get_save("時間") in range(0,360):
            prompt += "at night,"
            negative += "(blue sky,twilight:1.3),"
        elif sjh.get_save("時間") in range(360,720):
            prompt += "day,"
            negative += "(night sky,night scene,twilight:1.3),"
        elif sjh.get_save("時間") in range(720,1060):
            prompt += "day,"
            negative += "(night sky,night scene,twilight:1.3),"
        elif sjh.get_save("時間") in range(1060,1150):
            prompt += "in the twilight,"
            negative += "(blue sky:1.3),"
        elif sjh.get_save("時間") >= 1150:
            prompt += "at night,"
            negative += "(blue sky,twilight:1.3),"


    # 置換機能の関数を呼ぶ
    # プロンプト中に%で囲まれた文字列があれば置換する機能
    # 失敗するとErrorというプロンプトが残る
    #CSVMで あとで対応
    ReplaceList= 'ReplaceList.csv'
    prompt = csvm.chikan(prompt)
    negative = csvm.chikan(negative)
    
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
def body_shape (sjh,flags):
    prompt = ""
    negative = ""
    csv_tal = 'Talent.csv'


    # 乳サイズ
    # 乳強調すると脱ぎたがるのどうしよう
    if flags["drawbreasts"] == 1:
        talents = ["絶壁","貧乳","巨乳","爆乳"]
        for tal in talents:
            if tal in sjh.get_save("talent"):
                prompt += csvm.get_df(csv_tal,"名称",tal,"プロンプト") + ","
                negative += csvm.get_df(csv_tal,"名称",tal,"ネガティブ") + ","

    # 体格、体型
    talents = ["小人体型","巨躯","小柄体型","ぽっちゃり","ムチムチ","スレンダー","がりがり"]
    for tal in talents:
        if tal in sjh.get_save("talent"):
            prompt += csvm.get_df(csv_tal,"名称",tal,"プロンプト") + ","
            negative += csvm.get_df(csv_tal,"名称",tal,"ネガティブ") + ","

    # 胸愛撫など、普通乳なのに巨乳に描かれがちなコマンドのときプロンプトにsmall breastsを付加する
    chk_list = ["爆乳","巨乳","貧乳","絶壁"]
    and_list = set(sjh.get_save('talent')) & set(chk_list)
    # リストに一致しないとき即ち普通乳のとき
    if (len(and_list)) == 0:
        # 胸愛撫、ぱふぱふ、後背位胸愛撫
        if str(sjh.get_save("コマンド")) in ("6","606","702"):
            prompt += "small breasts,"


    return prompt,negative

# 髪色
# def haircolor(sjh):
#     csvfile_path= csvm.find_csv_path('Talent.csv')
#     csv_tal = pd.read_csv(filepath_or_buffer=csvfile_path)
#     prompt = ""
#     negative = ""
#     talents = ["黒髪","栗毛","金髪","赤毛","銀髪","青髪","緑髪","ピンク髪","紫髪","白髪","オレンジ髪","水色髪","灰髪")
#     for tal in talents:
#         if tal in sjh.get_save("talent"):
#             # csvには色だけ書いてるのでhairをつける
#             prompt += csvm.get_df(csv_tal,"名称",tal,"プロンプト") + " hair,"
#             negative += csvm.get_df(csv_tal,"名称",tal,"ネガティブ") + " hair,"
#     return prompt


# 髪型 
def hairstyle(sjh):
    csv_tal = 'Talent.csv'
    prompt = ""
    negative = ""
    talents = ["長髪","セミロング","ショートカット","ポニーテール","ツインテール","サイドテール","縦ロール","ツインリング","三つ編み","短髪","おさげ髪","ポンパドール","ポニーアップ","サイドダウン","お団子髪","ツーサイドアップ","ダブルポニー","横ロール","まとめ髪","ボブカット","シニヨン","ロングヘア"]
    for tal in talents:
        if tal in sjh.get_save("talent"):
            prompt += csvm.get_df(csv_tal,"名称",tal,"プロンプト") + ","
            negative += csvm.get_df(csv_tal,"名称",tal,"ネガティブ") + ","
    return prompt,negative

# 一時装備､SEXTOY､状況による変化
# CSVを2列で検索する
def equipment(sjh,flags):
    prompt = ""
    negative = ""
    csv_equ = 'Equip.csv'

    N膣装備 = ["11","12","13","22"]
    Nアナル装備 = ["14","15","23"]    
    # 存在するすべてのequipについて繰り返す
    for key,value in sjh.get_save("equip").items():
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
        
        equ = csvm.get_df_2key(csv_equ,"TEQUIP",int(key),"値",int(value),"プロンプト")
        if  equ != "ERROR":
            prompt += equ + ","
        equ = csvm.get_df_2key(csv_equ,"TEQUIP",int(key),"値",int(value),"ネガティブ")
        if  equ != "ERROR":
            negative += equ + ","
        
    return prompt,negative

#ロケーション
def get_location(sjh):
    prompt = ""
    negative = ""

    # 700箇所
    csv_loc = 'Location.csv'
    
    prompt += csvm.get_df(csv_loc,"場所ID",sjh.get_save("CFLAG:MASTER:現在位置"),"プロンプト")
    prompt += ","
    negative += csvm.get_df(csv_loc,"場所ID",sjh.get_save("CFLAG:MASTER:現在位置"),"ネガティブ")
    negative += ","

    return prompt, negative

# 射精
def cumshot(sjh):
    射精箇所 = sjh.get_save("射精箇所")
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
        csvfile_path= csvm.find_csv_path('Effect.csv')
        csv_efc = pd.read_csv(filepath_or_buffer=csvfile_path)

        if sjh.get_save("MASTER射精量") <= 1:
            prompt += csvm.get_df(csv_efc,"名称","主人が射精","プロンプト") + ","
        else:
            prompt += csvm.get_df(csv_efc,"名称","主人が大量射精","プロンプト") + ","

    return prompt

#汚れ
def stain(sjh,flags):
    prompt = ""
    # if ((sjh.get_save("髪の汚れ") & 4)  == 4):
    #     prompt += "(facial,bukkake:1.2),"
    if flags["drawbreasts"] == 1:
        if (sjh.get_save("胸の汚れ") & 4)  == 4:
            prompt += "(cum on breasts),"
    if flags["drawvagina"] == 1:
        if (sjh.get_save("膣内射精フラグ")) >= 1:
            prompt += "cum drip from pussy,"
    return prompt
# cum on ～ はちんちんを誘発、semen on ～ はほとんど効果がない
# milkはときどきグラスが出る


# 解像度をcsvから読む
# シーン分岐ごとに読む
def get_kaizoudo(sjh):
    # TRAINとその他のEVENTで読み取るcsvが異なる
    if sjh.get_save("scene") == "TRAIN":
        csvfile = 'Train.csv'
        kaizoudo = str(csvm.get_df(csvfile,"コマンド番号",str(sjh.get_save("コマンド")),"解像度"))
    else:
        csvfile_path= csvm.find_csv_path('Event.csv')
        csvfile = pd.read_csv(filepath_or_buffer=csvfile_path)
        kaizoudo = str(csvm.get_df(csvfile,"名称",str(sjh.get_save("scene")),"解像度"))
        
    return kaizoudo

# 服装
def clothing(sjh, flags):
    prompt = ""
    negative = ""
    csv_clo = 'Cloth.csv'
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
    if sjh.get_save("コマンド") in ["1","8","9","40","41","42","44","45","46","60","61","62","63","64","65","66","67","68","69","70","71","72","83","100"]:
        下半身はだけフラグ = 1

    # 下着1（貞操帯、絆創膏、ニプレス）は未実装


    # ブラ露出判定
    # 上着が0枚 or 上着1枚かつ脱衣中 に露出フラグが立つ。ノーブラの判定はあとでやる
    if 上半身上着重ね着数(sjh) == 0 or (上半身上着重ね着数(sjh) == 1 and sjh.get_save("コマンド") == N上半身脱衣_上着):
        ブラ露出フラグ = 1
    elif 上半身はだけフラグ == 1:
        ブラ露出フラグ = 1
    
    # パンツ露出判定　ブラと同様
    if 下半身上着重ね着数(sjh) == 0 or (下半身上着重ね着数(sjh) == 1 and sjh.get_save("コマンド") == N下半身脱衣_上着):
        パンツ露出フラグ = 1 
    elif 下半身はだけフラグ == 1:
        パンツ露出フラグ = 1
    
    # 乳露出判定
    # 着てない or ブラのみの状態から脱ぐ、または元々ノーブラの状態でブラが見える条件を満たす
    if sjh.get_save("上半身着衣状況") == 0 or (上半身上着重ね着数(sjh) == 0 and sjh.get_save("コマンド") == N上半身脱衣_下着) or (sjh.get_save("上半身下着2") == 0 and ブラ露出フラグ == 1):
        ブラ露出フラグ = 0
        乳露出フラグ = 1

    # 秘部露出判定
    # なにも履いてない or パンツだけ履いてるのを脱ぐ、または元々ノーパンの状態でパンツが見える条件を満たす
    if sjh.get_save("下半身着衣状況") == 0 or (下半身上着重ね着数(sjh) == 0 and sjh.get_save("コマンド") == N下半身脱衣_下着) or (sjh.get_save("下半身下着2") == 0 and パンツ露出フラグ == 1):
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
    if (sjh.get_save("下半身下着表示フラグ") == 0 and 乳露出フラグ == 0) or sjh.get_save("上半身はだけ状態") == 1:
        clothings = ["上半身上着1","上半身上着2","ボディースーツ","ワンピース","着物","レオタード"]
        for clo in clothings:
            clothName= sjh.get_save(clo)
            if sjh.get_save(clo) != 0:
                prompt += "(wearing " + " " + csvm.get_df(csv_clo,"衣類名",clothName,"プロンプト") + ":1.3),"
                negative += csvm.get_df(csv_clo,"衣類名",clothName,"ネガティブ") + ","

    # 下半身上着
    if (パンツ露出フラグ == 0 and 秘部露出フラグ == 0) or sjh.get_save("下半身ずらし状態") == 1:
        clothings = ["下半身上着1","下半身上着2","スカート"]
        for clo in clothings:
            clothName = str(sjh.get_save(clo))
            if sjh.get_save(clo) != 0:
                prompt += "(wearing " + " " + csvm.get_df(csv_clo,"衣類名",clothName,"プロンプト") + ":1.3),"
                negative += csvm.get_df(csv_clo,"衣類名",clothName,"ネガティブ") + ","


    if ブラ露出フラグ == 1:
        if sjh.get_save("上半身下着2") != 0:
            prompt += "(wearing " + " " + csvm.get_df(csv_clo,"衣類名",str(sjh.get_save("上半身下着2")),"プロンプト") + ":1.3),"

    if パンツ露出フラグ == 1:
        if sjh.get_save("下半身下着2") != 0:
            # パンツの種類は未対応
            
            prompt += "(wearing " + " panties:1.3),"

    # panty aside
    # 挿入とクンニ
    if (sjh.get_save("マスターがＶ挿入") != 0 )or(sjh.get_save("マスターがＡ挿入") != 0) or (sjh.get_save("コマンド") == "1"):
        if sjh.get_save("下半身下着2") != 0:
            prompt += "(naked pussy, pantie aside),"

    return prompt,negative


def 上半身上着重ね着数(sjh):
    return ((sjh.get_save("上半身上着1") != 0) + (sjh.get_save("上半身上着2") != 0) + (sjh.get_save("ボディースーツ") != 0) + (sjh.get_save("ワンピース") != 0) + (sjh.get_save("着物") != 0) + (sjh.get_save("レオタード") != 0))

def 下半身上着重ね着数(sjh):
    return ((sjh.get_save("下半身上着1") != 0) + (sjh.get_save("下半身上着2") != 0) + (sjh.get_save("スカート") != 0) + (sjh.get_save("ボディースーツ") != 0) + (sjh.get_save("ワンピース") + sjh.get_save("着物") != 0) + (sjh.get_save("レオタード") != 0))