from eraTW.emo import Expression
import re
from module.sub import get_width_and_height
from eraTW.cloth import get_cloth_dict
from eraTW.cloth import ClothFlags
from module.csv_manager import CSVMFactory
csvm = CSVMFactory.get_instance()


class PromptMaker:
    def __init__(self, sjh):
        self.sjh = sjh
        self.erascene = self.sjh.get_save("scene") #sceneは色んなところで読み込むので先に読み込んどく
        self.prompt =    {"situation":"", "weather":"","scene":"", "chara":"","cloth":"",\
                         "train": "","emotion": "","stain": "","潤滑": "","effect": "",\
                         "body": "","hair": ""}
        self.negative =  {"situation":"", "weather":"","scene":"", "chara":"","cloth":"",\
                         "train": "","emotion": "","stain": "","潤滑": "","effect": "",\
                         "body": "","hair": ""}
        self.width = 0
        self.height = 0
        self.flags = {"drawchara":0,"drawface":0,"drawbreasts":0,\
                      "drawvagina":0,"drawanus":0}
        self.csv_files  = {"location":'Location.csv',"weather":'Weather.csv',"cloth":'Cloth.csv',\
                           "train":'Train.csv',"talent":'Talent.csv',"event":'Event.csv',\
                           "equip":'Equip.csv',"chara":'Character.csv',"effect":'Effect.csv'}


    def get_csvname(self, key):
        return self.csv_files.get(key)


    def add_prompt(self, elements, prompt, nega):
        if elements not in self.prompt:
            raise KeyError(f" '{elements}' なんてプロンプト要素、ないぜ！")
        if elements not in self.negative:
            raise KeyError(f"ネガティブプロンプトに '{elements}' は存在しねぇ！")

        if prompt:
            self.prompt[elements] += prompt + ", " #末尾はカンマと空白
        if nega:
            self.negative[elements] += nega + ", "


    def update(self):
        # SaveJSONHandler の class dict の更新などの処理
        # 条件によりコマンド差し替え（乳サイズでパイズリ→ナイズリ
        # キャラ差し替え　EXフラグが立っていたらEXキャラ用の名前に変更する
        # など
        #SJH使う場合要らないかも あとで考える
        com = self.sjh.get_save("コマンド名")

        # 巨乳未満のキャラのパイズリはナイズリに変更
        # (ちんちんが隠れてしまうような描写は普乳を逸脱しているため)
        if not (("巨乳" in self.sjh.get_save("talent")) or ("爆乳" in self.sjh.get_save("talent"))):
            if com == "パイズリ":
                com = "ナイズリ"

        # 着衣時の胸愛撫はCHAKUMOMIのLoraを適用
        # キャラLoraと相性よくないみたいでつらい
        if self.sjh.get_save("上半身着衣状況") != 0:
            if com == "胸愛撫":
                com = "着衣胸愛撫"

        # 更新されたデータで data 属性を更新
        self.sjh.update_data("コマンド名", com)


    def create_situation_prompt(self):
        if self.erascene == "ターゲット切替" or \
            self.erascene == "マスター移動":

            if self.sjh.get_save("キャラ固有番号") == 0:
                self.add_prompt("situation", "(empty scene)", "(1girl:1.5)")
            else:
                self.add_prompt("situation", "1girl standing, detailed scenery in the background,", "")
                self.flags["drawchara"] = 1
                self.flags["drawface"] = 1


    def create_location_prompt(self):
        # 700箇所
        #IDとの整合はあとで確かめる
        master = self.sjh.get_save("CFLAG:MASTER:現在位置")
        loc = self.get_csvname("location")
        prompt = csvm.get_df(loc,"場所ID", master,"プロンプト")
        nega = csvm.get_df(loc,"場所ID", master,"ネガティブ")
        self.add_prompt("location", prompt, nega)


    def create_weather_prompt(self):
        天気 = self.sjh.get_save("天気")
        wea = self.get_csvname("location")
        prompt = csvm.get_df(wea,"場所ID", 天気,"プロンプト")
        nega = csvm.get_df(wea,"場所ID", 天気,"ネガティブ")

        # 昼夜の表現を追加
        時間 = self.sjh.get_save("時間")
        if 時間 in range(0, 360) or 時間 >= 1150:
            prompt += "at night,"
            nega += "(blue sky,twilight:1.3),"
        elif 時間 in range(360, 1060):
            prompt += "day,"
            nega += "(night sky,night scene,twilight:1.3),"
        elif 時間 in range(1060, 1150):
            prompt += "in the twilight,"
            nega += "(blue sky:1.3),"

        self.add_prompt("weather", prompt, nega)



    def create_train_prompt(self):
        tra = self.get_csvname("train")
        eve = self.get_csvname("event")
        com = self.sjh.get_save("コマンド名")

        #0 以上だと成功
        #あとで検証
        if self.sjh.get_save("success") < 0:
            deny = csvm.get_df(tra,"コマンド名",com,"拒否プロンプト")
            if deny != "ERROR":
                # 拒否プロンプトがERRORでない場合、拒否プロンプトを出力
                nega = csvm.get_df(tra,"コマンド名",com,"拒否ネガティブ")
                self.add_prompt("train", deny, nega)
                return
        else:
            # Train.csvに定義された体位から読み取ったキャラ描画、顔描画、胸描画のフラグ（0か1が入る)
            self.flags["drawchara"] =  csvm.get_df(tra,"コマンド名",com,"キャラ描画")
            self.flags["drawface"] =  csvm.get_df(tra,"コマンド名",com,"顔描画")
            self.flags["drawbreasts"] =  csvm.get_df(tra,"コマンド名",com,"胸描画")
            self.flags["drawvagina"] = csvm.get_df(tra,"コマンド名",com,"ヴァギナ描画")
            self.flags["drawanus"] = csvm.get_df(tra,"コマンド名",com,"アナル描画")

            # コマンドが未記入の場合はget_dfが"ERROR"を返すのでEvent.csvの汎用調教を呼ぶ
            prompt = csvm.get_df(tra,"コマンド名",com,"プロンプト")
            if prompt == "ERROR":
                prompt += csvm.get_df(eve,"名称","汎用調教","プロンプト")
                nega += csvm.get_df(eve,"名称","汎用調教","ネガティブ")

                self.flags["drawchara"] = csvm.get_df(eve,"名称","汎用調教","キャラ描画")
                self.flags["drawface"] = csvm.get_df(eve,"名称","汎用調教","顔描画")
                self.flags["drawbreasts"] = csvm.get_df(eve,"名称","汎用調教","胸描画")
                self.flags["drawvagina"] = csvm.get_df(eve,"名称","汎用調教","ヴァギナ描画")
                self.flags["drawanus"] = csvm.get_df(eve,"名称","汎用調教","アナル描画")

                self.add_prompt("train", prompt, nega)


    # 一時装備､SEXTOY､状況による変化
    #tequipとしたほうがera変数との整合性で見やすいか? あとで見直す
    # CSVを2列で検索する
    #create_train_promptより必ず後で呼び出さないとフラグが無意味になる
    def ecreate_equip_prompt(self):
        equ = self.get_csvname("equip.csv")

        N膣装備 = ["11","12","13","22"]
        Nアナル装備 = ["14","15","23"]
        #装備の値はあとで確認
        # 存在するすべてのequipについて繰り返す
        for key,value in self.sjh.get_save("tequip").items():
            # 構図による装備品のスキップ
            if key in N膣装備:
                print("v")
                print(self.flags["drawvagina"])
                if self.flags["drawvagina"] == 0:
                    continue
            if key in Nアナル装備:
                print("a")
                print(self.flags["drawanus"])
                if self.flags["drawanus"] == 0:
                    continue

            if key > 11: #eraTWでtequipで意味ある数字は11以上
                prompt = csvm.get_df_2key(equ,"TEQUIP",int(key),"値",int(value),"プロンプト")
                if  prompt == "ERROR":
                    continue
                nega = csvm.get_df_2key(equ,"TEQUIP",int(key),"値",int(value),"ネガティブ")
                self.add_prompt("equip", prompt, nega)


    def create_stain_prompt(self):
        # 付着した精液
        #装備 調教対象キャラが映るときのみ
        if self.flags["drawchara"] == 1:
            self.ecreate_equip_prompt()

        if self.flags["drawbreasts"] == 1:
            if (self.sjh.get_save("胸の汚れ") & 4)  == 4:
                self.add_prompt("stain", "(cum on breasts)", None)
        if self.flags["drawvagina"] == 1:
            if (self.sjh.get_save("膣内射精フラグ")) >= 1:
                self.add_prompt("stain", "cum drip from pussy", None)

        # cum on ～ はちんちんを誘発、semen on ～ はほとんど効果がない
        # milkはときどきグラスが出る


    def create_chara_prompt(self):
        cha = self.get_csvname("chara")
        efc = self.get_csvname("effect")

        # キャラ描写で毎回記述するプロンプト Effect.csvから読み出す
        charabase = csvm.get_df(efc,"名称","人物プロンプト","プロンプト")
        self.add_prompt("chara", charabase, "")

        # 特別な名前でプロンプトを登録してある場合、キャラ描写を強制的に上書きする処理
        uwagaki = csvm.get_df(cha,"キャラ名","描画キャラ上書き","プロンプト")
        if uwagaki != "EROOR": #EROORじゃなかったら上書き
            prompt = "\(" + uwagaki + "\)"
            nega = csvm.get_df(cha,"キャラ名","描画キャラ上書き","ネガティブ")
            self.add_prompt("chara", prompt, nega)

        else:
            #割り込みがなければ通常のキャラプロンプト読み込み処理
            name = self.sjh.get_save("target")
            prompt = "\(" + csvm.get_df(cha,"キャラ名",name,"プロンプト") + ":"\
                           + csvm.get_df(cha,"キャラ名",name,"プロンプト強調") + "\), "
            prompt += "\(" + csvm.get_df(cha,"キャラ名",name,"プロンプト2") + "\), "
            prompt += csvm.get_df(cha,"キャラ名",name,"キャラLora")
            nega += csvm.get_df(cha,"キャラ名",name,"ネガティブ")
            self.add_prompt("chara", prompt, nega)


    def create_cum_prompt(self):
        射精箇所 = self.sjh.get_save("射精箇所")
        efc = self.get_csvname("effect")
        #;TFLAG:1 射精箇所 (ビット0=コンドーム 1=膣内 2=アナル 3=手淫 4=口淫 5=パイズリ 6=素股 7=足コキ 8=体表 9=アナル奉仕
        #なにこれ? → 20=手淫フェラ 21=パイズリフェラ22=シックスナイン 24=子宮口 25=疑似 26=授乳プレイ
        # チェックするビット位置のリスト
        ejaculation_places = {
                1: "(cum in pussy,internal ejaculation)",
                2: "(cum in ass)",
                4: "(cum on hand, ejaculation, projectile cum)",
                8: "(cum in mouth)",
                16: "(cum on breasts, ejaculation, projectile cum)",
                32: "(cum on lower body, ejaculation, projectile cum)",
                64: "(cum on feet, ejaculation, projectile cum)",
                128: "(cum on stomach, ejaculation, projectile cum)",
                256: "(ejaculation, projectile cum)"
            }
        for bit, description in ejaculation_places.items():
            if 射精箇所 & bit != 0:
                cumin = description
                if self.sjh.get_save("MASTER射精量") <= 1:
                    prompt = csvm.get_df(efc,"名称","主人が射精","プロンプト")
                else:
                    prompt = csvm.get_df(efc,"名称","主人が大量射精","プロンプト")

                prompt += cumin
                self.add_prompt("stain", prompt, None)


    def create_juice_prompt(self):
        #TRAIN限定のエフェクト
        # ヴァギナ描画onのとき
        if self.flags["drawvagina"] == 1:
            # 潤滑度に基づいてプロンプトを追加
            潤滑度 = self.sjh.get_save("palam")["潤滑"]
            if 潤滑度 < 200:
                self.add_prompt("潤滑", None, "pussy juice")
            elif 1000 <= 潤滑度 < 2500:
                self.add_prompt("潤滑", "pussy juice", None)
            elif 2500 <= 潤滑度 < 5000:
                self.add_prompt("潤滑", "dripping pussy juice", None)
            else:
                self.add_prompt("潤滑", "(dripping pussy juice)", None)



    def create_traineffect_prompt(self):
        #TRAIN限定のエフェクト
        # エフェクト等 TFLAGは調教終了時には初期化されない。TRAINに限定しないと料理中に射精とかが起こる
        efc = self.get_csvname("effect")
        # 破瓜の血
        if self.sjh.get_save("処女喪失") > 0:
            prompt = csvm.get_df(efc,"名称","処女喪失","プロンプト")
            self.add_prompt("effect", prompt, None)
        if self.sjh.get_save("今回の調教で処女喪失") > 0:
            prompt = csvm.get_df(efc,"名称","今回の調教で処女喪失","プロンプト")
            self.add_prompt("effect", prompt, None)
        if self.sjh.get_save("放尿") > 0:
            prompt = csvm.get_df(efc,"名称","放尿","プロンプト")
            self.add_prompt("effect", prompt, None)
        if self.flags["drawbreasts"]:
            if self.sjh.get_save("噴乳") > 0:
                prompt = csvm.get_df(efc,"名称","噴乳","プロンプト")
                self.add_prompt("effect", prompt, None)


    def create_effect_prompt(self):
        efc = self.get_csvname("effect")
        if "妊娠" in self.sjh.get_save("talent"):
            # 標準で20日で出産する。残14日から描写し、残8日でさらに進行
            if (self.sjh.get_save("出産日") - self.sjh.get_save("日付")) in range(8,14):
                prompt = csvm.get_df(efc,"名称","妊娠中期","プロンプト")
            elif (self.sjh.get_save("出産日") - self.sjh.get_save("日付")) <= 8:
                prompt = csvm.get_df(efc,"名称","妊娠後期","プロンプト")
                self.add_prompt("effect", prompt, None)


    def create_eyes_prompt(self):
        #目の色をクラス辞書に追記しておく
        cha = self.get_csvname("chara")
        prompt = csvm.get_df(cha,"キャラ名",self.sjh.get_save("target"),"目の色")
        self.add_prompt("chara", prompt, None)



    def create_body_prompt(self):
        tal = self.get_csvname("talent")

        # 乳サイズ
        if self.flags["drawbreasts"] == 1:
            talents = ["絶壁","貧乳","巨乳","爆乳"]
            for tal in talents:
                if tal in self.sjh.get_save("talent"):
                    prompt = csvm.get_df(tal,"名称",tal,"プロンプト")
                    nega = csvm.get_df(tal,"名称",tal,"ネガティブ")
                    self.add_prompt("body", prompt, nega)
        else:
            talents = ["絶壁","貧乳","巨乳","爆乳"]
            for tal in talents:
                if tal in self.sjh.get_save("talent"):
                    prompt = csvm.get_df(tal,"名称",tal,"プロンプト")
                    nega = csvm.get_df(tal,"名称",tal,"ネガティブ")
                    nega += ", areolae, nipple" #negaが空白だった時用対策
                    self.add_prompt("body", prompt, nega)

        # 体格、体型
        talents = ["小人体型","巨躯","小柄体型","ぽっちゃり","ムチムチ","スレンダー","がりがり"]
        for tal in talents:
            if tal in self.sjh.get_save("talent"):
                prompt = csvm.get_df(tal,"名称",tal,"プロンプト")
                nega = csvm.get_df(tal,"名称",tal,"ネガティブ")
                self.add_prompt("body", prompt, nega)


        # 胸愛撫など、普通乳なのに巨乳に描かれがちなコマンドのときプロンプトにsmall breastsを付加する
        chk_list = ["爆乳","巨乳","貧乳","絶壁"]
        and_list = set(self.sjh.get_save('talent')) & set(chk_list)
        # リストに一致しないとき即ち普通乳のとき
        if (len(and_list)) == 0:
            # 胸愛撫、ぱふぱふ、後背位胸愛撫
            if self.sjh.get_save("コマンド") in ("6","606","702"):
                self.add_prompt("body", "small breasts", None)


    def create_hair_prompt(self):
        tal = self.get_csvname("talent")
        talents = ["長髪","セミロング","ショートカット","ポニーテール","ツインテール",\
                   "サイドテール","縦ロール","ツインリング","三つ編み","短髪","おさげ髪",\
                   "ポンパドール","ポニーアップ","サイドダウン","お団子髪","ツーサイドアップ",\
                   "ダブルポニー","横ロール","まとめ髪","ボブカット","シニヨン","ロングヘア"]
        for tal in talents:
            if tal in self.sjh.get_save("talent"):
                prompt = csvm.get_df(tal,"名称",tal,"プロンプト")
                nega = csvm.get_df(tal,"名称",tal,"ネガティブ")
                self.add_prompt("hair", prompt, nega)


    # 解像度をcsvから読む
    def get_kaizoudo(self):
        # TRAINとその他のEVENTで読み取るcsvが異なる
        if self.erascene == "TRAIN":
            tra = self.get_csvname("train")
            kaizoudo = csvm.get_df(tra,"コマンド名",self.sjh.get_save("コマンド"),"解像度")
        else:
            eve = self.get_csvname("event")
            kaizoudo = csvm.get_df(eve,"名称",self.erascene,"解像度")
            self.width, self.height = get_width_and_height(kaizoudo)



    # 服装
    def clothing(self):
        clo = self.get_csvname("cloth")

        #グラグの処理はクラスにまとめる
        cf = ClothFlags(self.sjh)
        #TARGETの現在の装備一覧 dict
        cloth_dict = get_cloth_dict(self.sjh)

        #ノーパンノーブラ判定 bool
        nop = cf.nopan()
        nob = cf.nobura()
        #eはexposed は露出の e
        nippse = cf.nipps_exposed()
        pussye = cf.pussy_exposed()
        burae = cf.bra_exposed()
        pantse = cf.psnts_exposed()

        # 上着描写
        # 上半身上着
        if (self.sjh.get_save("下半身下着表示フラグ") == 0 and nippse == 0)\
            or self.sjh.get_save("上半身はだけ状態") == 1:
            clothings = ["上半身上着1","上半身上着2","ボディースーツ","ワンピース","着物","レオタード"]
            for clo in clothings:
                name= self.sjh.get_save(clo)
                if self.sjh.get_save(clo) != 0:
                    prompt = csvm.get_df(clo,"衣類名",name,"プロンプト")
                    prompt = "(wearing " + prompt + ":1.3)"
                    nega = csvm.get_df(clo,"衣類名",name,"ネガティブ")
                    self.add_prompt("cloth", prompt, nega)

        # 下半身上着
        if (pantse == 0 and pussye == 0)\
            or self.sjh.get_save("下半身ずらし状態") == 1:
            clothings = ["下半身上着1","下半身上着2","スカート"]
            for clo in clothings:
                name = self.sjh.get_save(clo)
                if self.sjh.get_save(clo) != 0:
                    prompt = csvm.get_df(clo,"衣類名",name,"プロンプト")
                    prompt = "(wearing " + prompt + ":1.3)"
                    nega = csvm.get_df(clo,"衣類名",name,"ネガティブ")
                    self.add_prompt("cloth", prompt, nega)


        if burae == 1:
            if self.sjh.get_save("上半身下着2") != 0:
                prompt = csvm.get_df(clo,"衣類名",self.sjh.get_save("upper_underwear"),"プロンプト")
                prompt = "(wearing " + prompt + ":1.3)"
                self.add_prompt("cloth", prompt, None)

        if pantse == 1:
            if self.sjh.get_save("下半身下着2") != 0:
                prompt = csvm.get_df(clo,"衣類名",self.sjh.get_save("lower_underwear"),"プロンプト")
                prompt = "(wearing "+ prompt + " panties:1.3),"
                self.add_prompt("cloth", prompt, None)

        # panty aside
        # 挿入とクンニ
        if (self.sjh.get_save("マスターがＶ挿入") != 0 )\
            or(self.sjh.get_save("マスターがＡ挿入") != 0)\
            or (self.sjh.get_save("コマンド") == "1"):
            if self.sjh.get_save("下半身下着2") != 0:
                self.add_prompt("cloth", "(pantie aside)", None)

        # キャラ描写の前にBREAKしておく？これいいのか悪いのかわからぬ
        # prompt += "BREAK,"













    #     #表情ブレンダー
    #     p,n = Expression(sjh,flags)
    #     prompt += p
    #     negative += n
    # #ここまでキャラ描画フラグがonのときの処理



    # # 置換機能の関数を呼ぶ
    # # プロンプト中に%で囲まれた文字列があれば置換する機能
    # # 失敗するとErrorというプロンプトが残る
    # prompt = csvm.chikan(prompt)
    # negative = csvm.chikan(negative)


    # # 重複カンマを1つにまとめる
    # prompt = re.sub(',+',',',prompt)
    # negative = re.sub(',+',',',negative)

    # return prompt,negative,gen_width,gen_height
# *********************************************************************************************************
# ----------ここまでpromptmaker----------------------------------------------------------------------------------
# *********************************************************************************************************
