import pandas as pd
import os
from module.emo import Expression
import re
from module.csv_manager import CSVMFactory
csvm = CSVMFactory.get_instance()
from module.sub import get_width_and_height

# あとでcsvから読むように変更する
N挿入Gスポ責め = "614"
N挿入子宮口責め = "615"
N正常位 = "20"
N対面座位 = "22"
N対面立位 = "27"
N後背位 = "21"
N背面座位 = "23"
N背面立位 = "28"
Nパイズリ = "42"
Nナイズリ = "56"

# order自体を変化させる前処理
# たとえば
# 条件によりコマンド差し替え（乳サイズでパイズリ→ナイズリ
# キャラ差し替え　EXフラグが立っていたらEXキャラ用の名前に変更する
# など
def preceding(sjh):
    comNo = sjh.get_save("コマンド")
    prev = sjh.get_save("前回コマンド")
    # コマンドの差し替え
    # 挿入Gスポ責め/挿入子宮口責めのとき、派生元により前からアングルか後ろからアングルかで変更
    if comNo in (N挿入Gスポ責め,N挿入子宮口責め):
        if prev in (N正常位,N対面座位,N対面立位):
            comNo = N挿入Gスポ責め
        elif prev in (N後背位,N背面座位,N背面立位):
            comNo = N挿入子宮口責め

    # 巨乳未満のキャラのパイズリはナイズリに変更
    # (ちんちんが隠れてしまうような描写は普乳を逸脱しているため)
    if not (("巨乳" in sjh.get_save("talent")) or ("爆乳" in sjh.get_save("talent"))):
        if comNo == Nパイズリ:
                comNo = Nナイズリ

    # 更新されたデータで data 属性を更新
    sjh.update_data("コマンド",comNo)

    # メモ　EXキャラに変更するときはCFLAG:0をみてtargetを変更する。未実装
    return sjh

# orderをもとにプロンプトを整形する関数
def promptmaker(sjh):
    
    # orderを変化させる事前処理 コマンドが変われば解像度の変化もありえる
    sjh = preceding(sjh)

    kaizoudo = ""
    gen_width = 0
    gen_height = 0

    prompt = ""
    negative = ""

    flags = {"drawchara":0,"drawface":0,"drawbreasts":0,"drawvagina":0,"drawanus":0}

    flags["主人以外が相手"] = 0
    csv_eve = 'Event.csv'
    if sjh.get_save("scene") != "TRAIN" and csvm.get_df(csv_eve,"名称",sjh.get_save("scene"),"主人以外が相手") == 1:
        flags["主人以外が相手"] = 1

    # Effect.csvとEvent.csvは起動時に読み込んだ
    csv_efc = 'Effect.csv'
    csv_eve = 'Event.csv'

    prompt += csvm.get_df(csv_efc,'名称','基礎プロンプト','プロンプト') + ","
    negative += csvm.get_df(csv_efc,'名称','基礎プロンプト','ネガティブ')  + ","

    if "死亡" in sjh.get_save("talent"):
        prompt += "tombstone,dark scene,offering of flowers,"
        negative += "girl,"
        return prompt, negative,0,0

    #シーン分岐
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
            # コマンド成否で分岐
            # 成否判定のないコマンドの場合、sjh.get_save("success"]の値は不定(前回コマンドのまま)
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
        prompt += stain(sjh,flags)
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

    #------------ここまでTRAIN-ここからBEFORE---------------------
    if sjh.get_save("scene") == "BEFORE" :
        #今のところ一般シーンとやってること同じ
        flags["drawchara"] = csvm.get_df(csv_eve,"名称","BEFORE","キャラ描画")
        flags["drawface"] = csvm.get_df(csv_eve,"名称","BEFORE","顔描画")
        flags["drawbreasts"] = csvm.get_df(csv_eve,"名称","BEFORE","胸描画")
        flags["drawvagina"] = csvm.get_df(csv_eve,"名称","BEFORE","ヴァギナ描画")
        flags["drawanus"] = csvm.get_df(csv_eve,"名称","BEFORE","アナル描画")
        prompt += csvm.get_df(csv_eve,"名称","BEFORE","プロンプト") + ","
        negative += csvm.get_df(csv_eve,"名称","BEFORE","ネガティブ") + ","

        # 調教開始前は装備なし
        #ロケーション
        #YMは調教部屋固定？他にあれば追加
        p,n = get_location(sjh)
        prompt += p
        negative += n

        #解像度
        kaizoudo = get_kaizoudo(sjh)

    #------------ここまでBEFORE-ここからAFTER---------------------
    if sjh.get_save("scene") == "AFTER" :

        #余裕を持って終わったとき　座る
        #気力体力を消耗しているとき　寝る
        #恋慕のときは特別な構図
        #体力を使い切ったら　事後Loraを適用

        #恋慕で余力のあるときは添い寝
        if ("恋慕" in sjh.get_save("talent")) and (sjh.get_save("体力") >= 500):
            Scene = "AFTERピロートーク"
        else:
            # 軽い調教なら座る
            if (sjh.get_save("体力") >= 1300) or (sjh.get_save("気力")) >= 500:
                Scene = "AFTER"
            else:
            #疲れたら寝る
                Scene = "AFTER疲労"
                        
                #体力がなくなるまで調教した
                if (sjh.get_save("体力") < 550) and (sjh.get_save("気力") < 100):
                    prompt += csvm.get_df(csv_efc,"名称","AFTER用事後Lora","プロンプト") + ","
                    negative += csvm.get_df(csv_efc,"名称","AFTER用事後Lora","ネガティブ") + ","

                #膣内射精があると事後感を出す
                if sjh.get_save("膣内射精フラグ") > 0:
                    prompt += csvm.get_df(csv_efc,"名称","AFTER用精液溢れ","プロンプト") + ","
                    # if sjh.get_save("今回の調教で処女喪失"] > 0:
                    #     prompt += "(milk and blood from pussy:1.4)"
                    ## いい表現が見つかったら


        prompt += csvm.get_df(csv_eve,"名称",Scene,"プロンプト") + ","
        negative += csvm.get_df(csv_eve,"名称",Scene,"ネガティブ") + ","

        flags["drawchara"] = csvm.get_df(csv_eve,"名称",Scene,"キャラ描画")
        flags["drawface"] = csvm.get_df(csv_eve,"名称",Scene,"顔描画")
        flags["drawbreasts"] = csvm.get_df(csv_eve,"名称",Scene,"胸描画")
        flags["drawvagina"] = csvm.get_df(csv_eve,"名称",Scene,"ヴァギナ描画")
        flags["drawanus"] = csvm.get_df(csv_eve,"名称",Scene,"アナル描画")    

        # 付着した精液
        prompt += stain(sjh,flags)
        #装備
        p,n = equipment(sjh,flags)
        prompt += p
        negative += n
        #ロケーション
        p,n = get_location(sjh)
        prompt += p
        negative += n

        # 解像度
        # 上で分岐したSceneで見る。get_kaizoudoを呼ばずに直接書く。
        csvfile = 'Event.csv'
        kaizoudo = csvm.get_df(csvfile,"名称",Scene,"解像度")
        
        #シーンの上書きはこちらに移動
        sjh.update_data("scene", "None")  # 更新された辞書でsceneを更新



    #------------ここまでAFTER-ここから一般イベント---------------------
    #特殊イベントでないときは"scene"の値でcsvを検索する
    if not sjh.get_save("scene") in ["BEFORE","TRAIN","AFTER"]:
        Scene = sjh.get_save("scene")

        flags["drawchara"] = csvm.get_df(csv_eve,"名称",Scene,"キャラ描画")
        flags["drawface"] = csvm.get_df(csv_eve,"名称",Scene,"顔描画")
        flags["drawbreasts"] = csvm.get_df(csv_eve,"名称",Scene,"胸描画")
        flags["drawvagina"] = csvm.get_df(csv_eve,"名称",Scene,"ヴァギナ描画")
        flags["drawanus"] = csvm.get_df(csv_eve,"名称",Scene,"アナル描画")

        prompt += csvm.get_df(csv_eve,"名称",Scene,"プロンプト")
        prompt += ","
        negative += csvm.get_df(csv_eve,"名称",Scene,"ネガティブ")  
        negative += ","

        #装備、ロケーションいることある？
        
        #解像度
        kaizoudo = get_kaizoudo(sjh)

    #------------ここまで一般イベント--------------------
    #シーン分岐はここまで

    #キャラ描写
    if flags["drawchara"] == 1:

        # キャラ描写の前にBREAKしておく
        prompt += "BREAK,"

        # キャラ描写で毎回記述するプロンプト Effect.csvから読み出す
        prompt += csvm.get_df(csv_efc,"名称","人物プロンプト","プロンプト") + ","

        # Character.csvとAdd_character.csvを結合はCSVM
        csv_cha = 'Character.csv'
        

        # 特別な名前でプロンプトを登録してある場合、キャラ描写を強制的に上書きする処理
        uwagaki = csvm.get_df(csv_cha,"キャラ名","描画キャラ上書き","プロンプト")
        if uwagaki != "": #空欄じゃなかったら上書き
            prompt += "\(" + uwagaki + "\),"
            negative += csvm.get_df(csv_cha,"キャラ名","描画キャラ上書き","ネガティブ") + ","
        else:
            #割り込みがなければ通常のキャラプロンプト読み込み処理
            chaName = sjh.get_save("target")
            prompt += "\(" + csvm.get_df(csv_cha,"キャラ名",chaName,"プロンプト") + "\),"
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
                if sjh.get_save("処女喪失") > 0:
                    prompt += csvm.get_df(csv_efc,"名称","処女喪失","プロンプト") + ","
                if sjh.get_save("今回の調教で処女喪失") > 0:
                    prompt += csvm.get_df(csv_efc,"名称","今回の調教で処女喪失","プロンプト") + ","            
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
        if (sjh.get_save("キャラ固有番号") in range(3000,4000)) or (sjh.get_save("キャラ固有番号") in (2048,2049)):
            prompt += haircolor(sjh)

        #髪型の関数
        p,n = hairstyle(sjh)
        prompt += p
        negative += n        

        #目の色をorderに追記しておく(Expression関数でclosed eyesの判定をした後に反映する)
        current_data = csvm.get_df(csv_cha,"キャラ名",sjh.get_save("target"),"目の色")
        sjh.update_data("eyecolor", current_data)
        
        #表情ブレンダー
        p,n = Expression(sjh,flags)
        prompt += p
        negative += n
    #ここまでキャラ描画フラグがonのときの処理



    # 昼夜の表現 屋外のみ
    # epuip52が野外プレイフラグ
    if (sjh.get_save("scene") in ["ライブ0","ライブ1"]) or ("52" in sjh.get_save("equip")):
        # 旧地獄市街や月の都に青空はないはず
        if "52" in sjh.get_save("equip") and sjh.get_save("野外プレイの場所") in (7,11):
            prompt += "at night"
        elif sjh.get_save("時間") == 0:
            prompt += "at noon"
        else:
            prompt += "at night"


    # 置換機能の関数を呼ぶ
    # プロンプト中に%で囲まれた文字列があれば置換する機能
    # 失敗するとErrorというプロンプトが残る
    prompt = csvm.chikan(prompt)
    negative = csvm.chikan(negative)
    
    # 解像度文字列を解釈する関数
    gen_width,gen_height = get_width_and_height(kaizoudo)

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
        if sjh.get_save("コマンド") in ("3","340","616"):
            prompt += "small breasts,"


    return prompt,negative

# 髪色
def haircolor(sjh):
    csv_tal = 'Talent.csv'
    prompt = ""
    negative = ""
    talents = ["黒髪","栗毛","金髪","赤毛","銀髪","青髪","緑髪","ピンク髪","紫髪","白髪","オレンジ髪","水色髪","灰髪"]
    for tal in talents:
        if tal in sjh.get_save("talent"):
            # csvには色だけ書いてるのでhairをつける
            prompt += csvm.get_df(csv_tal,"名称",tal,"プロンプト") + " hair,"
            negative += csvm.get_df(csv_tal,"名称",tal,"ネガティブ") + " hair,"
    return prompt


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

# 装備
# CSVを2列で検索する
def equipment(sjh,flags):
    prompt = ""
    negative = ""
    csv_equ = 'Equip.csv'
    
    N膣装備 = "20"
    Nアナル装備 = "25"    
    # 存在するすべてのequipについて繰り返す
    for key,value in sjh.get_save("equip").items():
        # 構図による装備品のスキップ
        if key == N膣装備:
            print("v")
            print(flags["drawvagina"])
            if flags["drawvagina"] == 0:
                continue
        if key == Nアナル装備:
            print("a")
            print(flags["drawanus"])
            if flags["drawanus"] == 0:
                continue
        
        equ = csvm.get_df_2key(csv_equ,"TEQUIP",key,"値",value,"プロンプト")
        if  equ != "ERROR":
            prompt += equ + ","
        equ = csvm.get_df_2key(csv_equ,"TEQUIP",key,"値",value,"ネガティブ")
        if  equ != "ERROR":
            negative += equ + ","
        
    return prompt,negative

#ロケーション
def get_location(sjh):
    prompt = ""
    negative = ""

    csv_loc = 'Location.csv'
    
    if sjh.get_save("scene") in ["TRAIN","AFTER"]:
        # TEQUIP:53 お風呂場プレイ
        if "53" in sjh.get_save("equip"):
            location = "お風呂場"
        # TEQUIP:53 野外プレイ
        elif "52" in sjh.get_save("equip"):
            # yagai1 のような文字列で指定する
            location = "yagai"+ sjh.get_save("野外プレイの場所")
            # ギャラリー
            if sjh.get_save("野外プレイの状況") == 1:
                prompt += "people in the background,passing by,"
            elif sjh.get_save("野外プレイの状況") == 2:
                prompt += "(people in the background,Surrounded by a crowd),"
            elif sjh.get_save("野外プレイの状況") >= 3:
                prompt += "(people in the background,Surrounded by a crowd,Attracting Attention:1.2),"
        else:
            location = "調教部屋"
    if sjh.get_save("scene") == "BEFORE": # BEFOREなら調教部屋
        location = "調教部屋"

    prompt += csvm.get_df(csv_loc,"名称",location,"プロンプト")
    prompt += ","
    negative += csvm.get_df(csv_loc,"名称",location,"ネガティブ")
    negative += ","

    return prompt, negative

# 射精
def cumshot(sjh):
    prompt = ""
    if sjh.get_save("膣内に射精") > 0:
        prompt += "(cum in pussy,internal ejaculation),"    
    if sjh.get_save("アナルに射精") > 0:
        prompt += "(cum in ass),"
    if sjh.get_save("髪に射精") > 0:
        prompt += "(cum on hair,projectile cum),"
    if sjh.get_save("顔に射精") > 0:
        prompt += "(cum on face,facial,projectile cum),"
    if sjh.get_save("口に射精") > 0:
        prompt += "(cum in mouth),"
    if sjh.get_save("胸に射精") > 0:
        prompt += "(cum on breasts,projectile cum),"
    if sjh.get_save("腹に射精") > 0:
        prompt += "(cum on stomach,projectile cum),"
    if sjh.get_save("腋に射精") > 0:
        prompt += "(cum on armpit,projectile cum),"
    if sjh.get_save("手に射精") > 0:
        prompt += "(cum on hand,projectile cum),"
    if sjh.get_save("秘裂に射精") > 0:
        prompt += "(cum on lower body,projectile cum),"
    if sjh.get_save("竿に射精") > 0:
        prompt += "(cum on penis,projectile cum),"
    if sjh.get_save("尻に射精") > 0:
        prompt += "(cum on ass,projectile cum),"
    if sjh.get_save("太腿に射精") > 0:
        prompt += "(cum on thigh,projectile cum),"
    if sjh.get_save("足で射精") > 0: # ここだけ「足 "で"」
        prompt += "(cum on feet,projectile cum),"
    #射精エフェクト
    if sjh.get_save("主人が射精") > 0:
        csvfile_path= os.path.join(os.path.dirname(__file__), 'csvfiles\\Effect.csv')
        csv_efc = pd.read_csv(filepath_or_buffer=csvfile_path)
        if sjh.get_save("主人が射精") == 1:
            prompt += csvm.get_df(csv_efc,"名称","主人が射精","プロンプト") + ","
        else:
            prompt += csvm.get_df(csv_efc,"名称","主人が大量射精","プロンプト") + ","
    return prompt

#汚れ
def stain(sjh,flags):
    prompt = ""
    if ((sjh.get_save("髪の汚れ") & 4)  == 4):
        prompt += "(facial,bukkake:1.2),"
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
        kaizoudo = csvm.get_df(csvfile,"コマンド番号",sjh.get_save("コマンド"),"解像度")
    else:
        csvfile = 'Event.csv'
        kaizoudo = csvm.get_df(csvfile,"名称",sjh.get_save("scene"),"解像度")
    
    return kaizoudo
