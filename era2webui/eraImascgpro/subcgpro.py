import random
from eraImascgpro.emoImascgpro import ExpressionImasCgpro
from module.promptmaker import PromptMaker
from module.csv_manager import CSVMFactory
csvm = CSVMFactory.get_instance()


class PromptMakerImascgpro(PromptMaker):
    """
    """
    def __init__(self, sjh):
        super().__init__(sjh)
        self.initialize_class_variablesimascgpro()


    def initialize_class_variablesimascgpro(self):
        #独自メソッド 独自の変数の初期化
        self.N挿入Gスポ責め = 614
        self.N挿入子宮口責め = 615
        self.N正常位 = 20
        self.N対面座位 = 22
        self.N対面立位 = 27
        self.N後背位 = 21
        self.N背面座位 = 23
        self.N背面立位 = 28
        self.Nパイズリ = 82
        self.Nナイズリ = 701
        self.N胸愛撫 = 6
        self.N着衣胸愛撫 = 702
        self.N膣装備 = 20
        self.Nアナル装備 = 25
        # 脱衣コマンドのコマンド番号
        self.N上半身脱衣_上着 = 200
        self.N下半身脱衣_上着 = 201
        self.N上半身脱衣_下着 = 202
        self.N下半身脱衣_下着 = 203
        # 体から離れた衣服の生成打率はいまだ著しく低いので、脱いでいる服の描写は未実装。脱衣コマンドを実行すると脱衣後の姿を表示する。
        # 決して諦めてはならない。

        self.flags["ブラ露出フラグ"] = False
        self.flags["パンツ露出フラグ"] = False
        self.flags["乳露出フラグ"] = False
        self.flags["秘部露出フラグ"] = False
        self.flags["上半身はだけフラグ"] = False #未実装 上着着衣のまま乳を見せるコマンド用
        self.flags["下半身はだけフラグ"] = False #スカート着衣のまま中身を見せるコマンド用


        self.comNo = self.sjh.get_save("コマンド")
        self.prev = self.sjh.get_save("前回コマンド")
        self.chaName = self.sjh.get_save("target")
        self.名前フラグ = self.sjh.get_save("名前フラグ")
        #saveの値で初期化しているがcreate_location_elementで判定後代入している
        self.location = self.sjh.get_save("野外プレイの場所")
        self.expose = self.sjh.get_save("野外プレイの状況")
        self.loca   = self.sjh.get_save("現在位置") #int
        self.hp = self.sjh.get_save("体力")
        self.equip = self.sjh.get_save("equip")
        self.palam_up = self.sjh.get_save("palam_up")
        self.hair_cum = self.sjh.get_save("髪の汚れ") #ビット演算
        self.b_cum = self.sjh.get_save("胸の汚れ") #ビット演算
        self.膣内に射精 = self.sjh.get_save("膣内に射精")
        self.アナルに射精 = self.sjh.get_save("アナルに射精")
        self.髪に射精 = self.sjh.get_save("髪に射精")
        self.顔に射精 = self.sjh.get_save("顔に射精")
        self.口に射精 = self.sjh.get_save("口に射精")
        self.胸に射精 = self.sjh.get_save("胸に射精")
        self.腹に射精 = self.sjh.get_save("腹に射精")
        self.腋に射精 = self.sjh.get_save("腋に射精")
        self.手に射精 = self.sjh.get_save("手に射精")
        self.秘裂に射精 = self.sjh.get_save("秘裂に射精")
        self.竿に射精 = self.sjh.get_save("竿に射精")
        self.尻に射精 = self.sjh.get_save("尻に射精")
        self.太腿に射精 = self.sjh.get_save("太腿に射精")
        self.足で射精 = self.sjh.get_save("足で射精")
        self.主人が射精 = self.sjh.get_save("主人が射精")
        self.不審者 = self.sjh.get_save("不審者") or 0
        self.下半身着衣状況 = self.sjh.get_save("下半身着衣状況")
        self.マスターがV挿入 = self.sjh.get_save("マスターがV挿入")
        self.マスターがA挿入 = self.sjh.get_save("マスターがA挿入")

        self.上半身上着1 = self.sjh.get_save("上半身上着1")
        self.上半身上着2 = self.sjh.get_save("上半身上着2")
        self.ボディースーツ = self.sjh.get_save("ボディースーツ")
        self.ワンピース = self.sjh.get_save("ワンピース")
        self.着物 = self.sjh.get_save("着物")
        self.レオタード = self.sjh.get_save("レオタード")
        self.下半身上着1 = self.sjh.get_save("下半身上着1")
        self.下半身上着2 = self.sjh.get_save("下半身上着2")
        self.下半身下着1 = self.sjh.get_save("下半身下着1")
        self.下半身下着2 = self.sjh.get_save("下半身上着2")
        self.スカート = self.sjh.get_save("スカート")
        self.上半身下着1 = self.sjh.get_save("上半身下着1")
        self.上半身下着2 = self.sjh.get_save("上半身下着2")


    def generate_prompt(self):
        """
        オーバーライド
        このgenerate_promptは、elementsをギュッと集めて呪文を生成するんだ。
        シチュエーション、ロケーション、天気、装備、キャラクターなど、色々な要素から呪文を組み立てていく。

        屋内か屋外かで天気の扱いが変わるし、TRAINシーンかどうかで処理も変わるんだ
        全部を合わせて、強力な呪文を作り上げるぜ。

        Returns:
            tuple: (prompt, negative, width, height)を返す。
                - prompt (str): シナリオに基づいた呪文のテキスト。
                - negative (str): 呪文のネガティブな面を表すテキスト。
                - width (int), height (int): 生成する画像のサイズ。

        このメソッドを使って、どんなシナリオにもバッチリ対応できる呪文を作れるぜ！
        """
        #呪文に含めるかの条件分岐はあとで考える
        self.create_situation_element() #シチュエーション｢マスター移動｣｢ターゲット切替｣
        self.create_location_element() #場所
        self.get_kaizoudo() #解像度
        self.create_timezone_element() #時間帯

        if self.scene == "TRAIN":
            self.create_train_element()#行動
            self.create_equip_element()#一時装備
            #TRAINに限定しないと料理中に射精とかが起こる
            self.create_cum_element()
            if self.flags["drawvagina"]:
                self.create_juice_element()#汁
                self.create_traineffect_element() #噴乳はここでない気がする あとで
                self.create_stain_element()#如何わしい汚れ

        #主人公しか居ない時はフラグをOFF 連れ出すときもOFFになる あとで
        if self.charno == 0:
            self.flags["drawchara"] = False
            self.flags["drawface"]  = False

        if self.flags["drawchara"]: # 人を描画しない場合は処理をスキップ
            self.create_chara_element() #キャラ
            self.create_body_element()  #体
            self.create_effect_element()#妊娠
            self.create_clothing_element()

        if self.flags["drawface"]:  # 顔を描画しない場合は処理をスキップ
            self.create_hair_element()#髪
            pm_var = self.gather_instance_data()
            emo= ExpressionImasCgpro(pm_var)
            emopro,emonega = emo.generate_emotion() #表情
            emo = ExpressionImasCgpro(self.sjh)
            emopro,emonega = emo.generate_emotion() #表情
            self.add_element("emotion", emopro, emonega)

        #辞書のvalueが空の要素を消す
        prompt_values = [value for value in self.prompt.values() if value.strip()]
        negative_values = [value for value in self.negative.values() if value.strip()]
        #カンマとスペースを足してヒトツナギに
        prompt = ", ".join(prompt_values)
        negative = ", ".join(negative_values)
        width = self.width
        height = self.height
        prompt = csvm.chikan(prompt)
        negative = csvm.chikan(negative)
        self.prompt_debug()
        return prompt,negative,width,height


    def update(self):
        """
        オーバーtライト imascgpro コマンド番号で動くように変更

        このメソッドは、SaveJSONHandlerのデータを適切に更新することで、シナリオのリアリティを高める役割を果たす。
        """
        # SaveJSONHandler の class dict の更新などの処理
        # 条件によりコマンド差し替え（乳サイズでパイズリ→ナイズリ
        # キャラ差し替え　EXフラグが立っていたらEXキャラ用の名前に変更する
        # など

        # 巨乳未満のキャラのパイズリはナイズリに変更
        # (ちんちんが隠れてしまうような描写は普乳を逸脱しているため)
        if not ("巨乳" in self.talent) or ("爆乳" in self.talent):
            if self.com ==  self.Nパイズリ:
                self.com = self.Nナイズリ

        # 着衣時の胸愛撫はCHAKUMOMIのLoraを適用
        # キャラLoraと相性よくないみたいでつらい
        if self.upwear != 0:
            if self.comNo == self.N胸愛撫:
                self.comNo = self.N着衣胸愛撫


    def create_situation_element(self):
        """
        オーバーライド
        不審者追加。
        # drawchara､drawface フラグの変更
        """
        eve = self.get_csvname("event")
        efc = self.get_csvname("effect")
        prompt = csvm.get_df(efc,"名称","基礎プロンプト","プロンプト")
        nega = csvm.get_df(efc,"名称","基礎プロンプト","ネガティブ")
        self.add_element("situation", prompt, nega)
        if self.scene == "ターゲット切替" or self.scene == "マスター移動" or self.scene == "真名看破":
            if self.charno == 0:
                    # targetがいないとき #この条件はTWではうまく動かない
                    self.add_element("situation", "(empty scene)", "(1girl:1.7)")

            else:
                self.add_element("situation", "1girl standing, detailed scenery in the background", None)
                #ターゲットが居るならキャラ｡顔表示ONにしないと誰かが居ても空っぽの場所になるよ
                self.flags["drawchara"] = True
                self.flags["drawface"] = True
                if self.不審者 == 1:
                    self.add_element("situation", ", (ugly man behind her in background:1.6)", None)

        #条件文は間違っていないがEvent.csvに主人以外が相手の列はない
        if csvm.get_df(eve,"名称",self.scene,"主人以外が相手") == 1 :
                self.flags["主人以外が相手"] = True


    def create_train_element(self):
        """
        オーバーライド 成否のロジックと検索条件が違う

        コマンドに対応するプロンプトを生成するんだ。
        CSVファイルから読み込んだコマンド番号に基づいて、適切なプロンプトとネガティブプロンプトを組み立てるぜ。

        行動が成功したか失敗したかによって処理が分岐するから、それもしっかりチェックしてくれよな。
        成功した場合は、CSVから読み込んだ情報に基づいてプロンプトを作成する。失敗した場合は、拒否プロンプトを使うんだ。
        # drawchara drawface drawbreasts drawvagina drawanus
        """
        tra = self.get_csvname("train")
        eve = self.get_csvname("event")


        #拒否プロンプトが空なら成否判定なしと判断、通常プロンプトを出力する
        deny = csvm.get_df(tra,"コマンド番号",self.comNo,"拒否プロンプト")
        if deny != "ERROR":
                # 拒否プロンプトがERRORでない場合、拒否プロンプトを出力
                nega = csvm.get_df(tra,"コマンド番号",self.comNo,"拒否ネガティブ")
                self.add_element("train", deny, nega)
                self.flags["drawchara"] = True
                self.flags["drawface"] = True
                return
        else:
            # Train.csvに定義された体位から読み取ったキャラ描画、顔描画、胸描画のフラグ（0か1が入る)
            #ブール値に変換
            self.flags["drawchara"] =  bool(csvm.get_df(tra,"コマンド番号",self.comNo,"キャラ描画"))
            self.flags["drawface"] =  bool(csvm.get_df(tra,"コマンド番号",self.comNo,"顔描画"))
            self.flags["drawbreasts"] =  bool(csvm.get_df(tra,"コマンド番号",self.comNo,"胸描画"))
            self.flags["drawvagina"] = bool(csvm.get_df(tra,"コマンド番号",self.comNo,"ヴァギナ描画"))
            self.flags["drawanus"] = bool(csvm.get_df(tra,"コマンド番号",self.comNo,"アナル描画"))

            # コマンドが未記入の場合はget_dfが"ERROR"を返すのでEvent.csvの汎用調教を呼ぶ
            prompt = csvm.get_df(tra,"コマンド番号",self.comNo,"プロンプト")
            if prompt == "ERROR":
                prompt = csvm.get_df(eve,"名称","汎用調教","プロンプト")
                nega = csvm.get_df(eve,"名称","汎用調教","ネガティブ")

                self.flags["drawchara"] = bool(csvm.get_df(eve,"名称","汎用調教","キャラ描画"))
                self.flags["drawface"] = bool(csvm.get_df(eve,"名称","汎用調教","顔描画"))
                self.flags["drawbreasts"] = bool(csvm.get_df(eve,"名称","汎用調教","胸描画"))
                self.flags["drawvagina"] = bool(csvm.get_df(eve,"名称","汎用調教","ヴァギナ描画"))
                self.flags["drawanus"] = bool(csvm.get_df(eve,"名称","汎用調教","アナル描画"))

                self.add_element("train", prompt, nega)
            nega = csvm.get_df(tra,"コマンド名",self.comNo,"ネガティブ")
            self.add_element("train", prompt, nega)


    def create_chara_element(self):
        """
        このcreate_chara_elementメソッドは、キャラクターの描画に関するプロンプトを生成するために使うんだ。
        CSVファイルからキャラクターに関するデータを読み込み、適切なプロンプトとネガティブプロンプトを追加するぜ。

        毎回記述されるキャラクターの基本的なプロンプトはEffect.csvから読み出す。
        さらに、特別な名前でプロンプトを登録してある場合は、キャラクター描写を強制的に上書きする処理も行うんだ。

        """
        cha = self.get_csvname("chara")
        efc = self.get_csvname("effect")

        # キャラ描写で毎回記述するプロンプト Effect.csvから読み出す
        charabase = csvm.get_df(efc,"名称","人物プロンプト","プロンプト")
        self.add_element("chara", charabase, None)

        # 特別な名前でプロンプトを登録してある場合、キャラ描写を強制的に上書きする処理
        uwagaki = csvm.get_df(cha,"キャラ名","描画キャラ上書き","プロンプト")
        if uwagaki != "ERROR": #EROORじゃなかったら上書き
            prompt = f"({uwagaki})"
            nega = csvm.get_df(cha,"キャラ名","描画キャラ上書き","ネガティブ")
            self.add_element("chara", prompt, nega)

        else:
            prompt = csvm.get_df(cha,"キャラ名",self.name,"プロンプト")
            prompt2 = csvm.get_df(cha,"キャラ名",self.name,"プロンプト2")
            # 未確定名のときは誰だかわからなくする
            if self.名前フラグ != 1:
                self.add_element("chara", "(pixel art:2.0),faceless female,(low quality,blurry:1.5)", None)
                self.add_element("chara", prompt2, None)

            #割り込みがなければ通常のキャラプロンプト読み込み処理
            prompt_wait = csvm.get_df(cha,"キャラ名",self.name,"プロンプト強調")
            # prompt_waitが"ERROR"でない場合にのみ結合する
            if prompt_wait != "ERROR":
                prompt = f"({prompt}:{prompt_wait})"
            self.add_element("chara", prompt, None)

            chara_lora = csvm.get_df(cha,"キャラ名",self.name,"キャラLora")
            nega = csvm.get_df(cha,"キャラ名",self.name,"ネガティブ")
            self.add_element("chara", chara_lora, nega)


    def create_equip_element(self):
        """
        このcreate_equip_elementメソッドは、現在のゲーム状況に合わせて装備品のプロンプトを生成するんだ。
        CSVファイルから装備品に関するデータを読み込み、適切なプロンプトとネガティブプロンプトを追加するぜ。

        装備品は、シーンの構図によって表示されるかどうかが変わる。
        だから、描画フラグに基づいて装備品をスキップする処理も行うんだ。
        こうすることで、シナリオのリアリティを高めることができるぜ！
        """
        equ = self.get_csvname("equip.csv")

        N膣装備 = [11,12,13,22]
        Nアナル装備 = [14,15,23]
        #装備の値はあとで確認
        # 存在するすべてのequipについて繰り返す
        for key,value in self.tequip.items():
            # 構図による装備品のスキップ
            if key in N膣装備:
                print("v")
                print(self.flags["drawvagina"])
                if not self.flags["drawvagina"]:
                    continue
            if key in Nアナル装備:
                print("a")
                print(self.flags["drawanus"])
                if not self.flags["drawanus"]:
                    continue

            if key > 11: #eraTWでtequipで意味ある数字は11以上
                prompt = csvm.get_df_2key(equ,"TEQUIP",int(key),"値",int(value),"プロンプト")
                if  prompt == "ERROR":
                    continue
                nega = csvm.get_df_2key(equ,"TEQUIP",int(key),"値",int(value),"ネガティブ")
                self.add_element("equip", prompt, nega)


    def create_location_element(self):
        """
        オーバーライド 私室描写の追加

        現在のシナリオに合わせて、ロケーションに関するプロンプトを生成するメソッドだぜ。
        CSVファイルからロケーションに関するデータを読み込み、適切なプロンプトとネガティブプロンプトを追加する。

        """
        if self.loca in range(72,300):
            self.add_element("location", ", in girl's private room,bed,desk,furniture", None)
        else:
            loc = self.get_csvname("location")
            prompt = csvm.get_df(loc,"番号", self.loca,"プロンプト")
            nega = csvm.get_df(loc,"番号", self.loca,"ネガティブ")
            self.add_element("location", prompt, nega)


    def create_clothing_element(self):
        """オーバーライド

        Returns:
            _type_: _description_
        """
        clo_csv = self.get_csvname("cloth")

        # 下半身はだけ　クンニ、秘貝開帳、自慰、ローター、Eマッサージャ、クリキャップ、バイブ、アナルバイブ、アナルビーズ、正常位、後背位、正常位アナル、後背位アナル、逆レイプ、騎乗位、騎乗位アナル、対面座位、背面座位、対面座位アナル、背面座位アナル、二穴挿し、素股、スパンキング、
        if self.comNo in [1,8,9,40,41,42,44,45,46,60,61,62,63,64,65,66,67,68,69,70,71,72,83,100]:
            self.flags["下半身はだけフラグ"] = True

        # 下着1（貞操帯、絆創膏、ニプレス）は未実装

        self.上半身上着重ね着数()
        self.下半身上着重ね着数()
        # ブラ露出判定
        # 上着が0枚 or 上着1枚かつ脱衣中 に露出フラグが立つ。ノーブラの判定はあとでやる
        if self.上枚数 == 0 or\
            self.上枚数 == 1 and self.comNo == self.N上半身脱衣_上着:
            self.flags["ブラ露出フラグ"] = True
        elif self.flags["上半身はだけフラグ"]:
            self.flags["ブラ露出フラグ"] = True

        # パンツ露出判定　ブラと同様
        if self.下枚数 == 0 or self.下枚数 == 1 and self.comNo == self.N下半身脱衣_上着:
            self.flags["パンツ露出フラグ"] = True
        elif self.flags["下半身はだけフラグ"]:
            self.flags["パンツ露出フラグ"] = True

        # 乳露出判定
        # 着てない or ブラのみの状態から脱ぐ、または元々ノーブラの状態でブラが見える条件を満たす
        if self.upwear == 0 or self.上枚数 == 0 and self.comNo == self.N上半身脱衣_下着\
            or self.上半身下着2 == 0 and self.flags["ブラ露出フラグ"]:
            self.flags["ブラ露出フラグ"] = False
            self.flags["乳露出フラグ"] = True

        # 秘部露出判定
        # なにも履いてない or パンツだけ履いてるのを脱ぐ、または元々ノーパンの状態でパンツが見える条件を満たす
        if self.下半身着衣状況 == 0 or self.下枚数 == 0 and self.comNo == self.N下半身脱衣_下着\
            or self.下半身下着2 == 0 and self.flags["パンツ露出フラグ"]:
            self.flags["パンツ露出フラグ"]  = False
            self.flags["秘部露出フラグ"] = True

        # 裸体描写
        # 上半身だけ着てる
        if self.flags["秘部露出フラグ"] and not self.flags["乳露出フラグ"]:
            prompt = "nsfw, her lower body is naked,(bottomless, naked clotch, pussy),"
            self.add_element("cloth", prompt, None)

        # 下半身だけ着てる
        if not self.flags["秘部露出フラグ"] and self.flags["乳露出フラグ"]:
            prompt += "nsfw, her upper body is naked,(topless, naked breasts, nipples),"
            self.add_element("cloth", prompt, None)
        # 全裸
        if self.flags["秘部露出フラグ"] and self.flags["乳露出フラグ"]:
            prompt += "nsfw, full nude,completely naked, (naked breasts,nipples),"
            self.add_element("cloth", prompt, None)


        # 上着描写
        # 上半身上着
        if not self.flags["ブラ露出フラグ"] and not self.flags["乳露出フラグ"]\
            or self.flags["上半身はだけフラグ"]:
            clothings = ["上半身上着1","上半身上着2","ボディースーツ","ワンピース","着物","レオタード"]
            for clothing_name in clothings:
                # 各服装に対応する属性の値を取得する。属性が存在しなければデフォルト値として 0 を返す。
                clothing_value = getattr(self, clothing_name, 0)
                if clothing_value != 0:
                    prompt = csvm.get_df(clo_csv,"番号", clothing_value, "プロンプト")
                    if prompt != "ERROR":
                        today_cloth = self.今日の服(clothing_value)
                        prompt = f"(wearing {today_cloth} {prompt}:1.3)"
                        negative = csvm.get_df(clo_csv,"番号",clothing_value,"ネガティブ")
                        self.add_element("cloth", prompt, negative)

        # 下半身上着
        if self.flags["パンツ露出フラグ"] == 0 and not self.flags["秘部露出フラグ"] or self.flags["下半身はだけフラグ"]:
            clothings = ["下半身上着1","下半身上着2","スカート"]
            for clothing_name in clothings:
                clothing_value = getattr(self, clothing_name, 0)
                if clothing_value != 0:
                    prompt = csvm.get_df(clo_csv,"番号", clothing_value, "プロンプト")
                    if prompt != "ERROR":
                        today_cloth = self.今日の服(clothing_value)
                        prompt = f"(wearing {today_cloth} {prompt}:1.3)"
                        negative = csvm.get_df(clo_csv,"番号",clothing_value,"ネガティブ")
                        self.add_element("cloth", prompt, negative)


        if self.flags["ブラ露出フラグ"]:
            if self.上半身下着2 != 0:
                    prompt = f"(wearing {prompt}:1.3)"
                    today_cloth = self.今日の服(8888)
                    prompt2 = today_cloth +  prompt
                    negative = csvm.get_df(clo_csv,"番号",clothing_value,"ネガティブ")
                    self.add_element("cloth", prompt2, negative)

        if self.flags["パンツ露出フラグ"] == 1:
            if self.下半身下着2 != 0:
                # パンツの種類は未対応
                    prompt = f"(wearing {prompt}:1.3)"
                    today_cloth = self.今日の服(8888)
                    prompt2 = today_cloth +  prompt
                    negative = csvm.get_df(clo_csv,"番号",clothing_value,"ネガティブ")
                    self.add_element("cloth", prompt2, negative)

        # panty aside
        # 挿入とクンニ
        if self.マスターがV挿入 != 0 or self.マスターがA挿入 != 0 or self.comNo == 1:
            if self.下半身下着2 != 0:
                self.add_element("cloth", "(naked pussy, pantie aside)", None)


    # 日付とキャラ番号を使った疑似乱数でその日の服の色形を固定する
    def 今日の服(self,clothNo):
        clothcolor = ""
        # 色決まってるようなやつは除外　ブルマ、白衣、ワイシャツ、体操服、スク水
        if not clothNo in [802,1210,1304,1322,1701]:
            clothcolor = ""
            random.seed(self.charno+self.days+clothNo)

            # 確率で水玉、ストライプ、チェック柄を入れてみるテスト
            ra = random.randrange(10)
            if ra == 0:
                clothcolor += "polka-dots "
            elif ra == 1:
                clothcolor += "stripes pattern "
            elif ra == 2:
                clothcolor += "plaid "

            colors = ["light blue","yellow","white","black","light green","pink","purple"]
            clothcolor += random.choice(colors)

        # ちひろさんは緑の服を着るべき
        if self.chaName == "千川ちひろ":
            if clothNo == 1204:
                clothcolor = "green"
            elif clothNo == 901:
                clothcolor = "black"
            # ワイシャツには色指定なし（white dress shirtになるとホワイトドレスになる)
            elif clothNo == 1304:
                clothcolor = ""

        # しまむーのブレザーは他の色を指定しても高確率で茶色になるので茶色しか着せない
        if self.chaName == "島村卯月":
            if clothNo == 1208:
                clothcolor = "brown"
            # 制服スカートも固定しようとしたが、このままだとブレザーを脱いだ瞬間にスカートの色が変化してしまう
            # 脱いだ服を保存してあるはずなのでそっちを見るように修正が必要
            # if clothNo == "902":
            #     if order["上半身上着1"] == 1208:
            #         clothcolor = "plaid red"
        return clothcolor


    def 上半身上着重ね着数(self):
        self.上枚数 = sum(bool(var) for var in [self.上半身上着1,self.上半身上着2,self.ボディースーツ,self.ワンピース,self.着物,self.レオタード])


    def 下半身上着重ね着数(self):
        self.下枚数 = sum(bool(var) for var in [self.下半身上着1,self.下半身上着2,self.スカート,self.ボディースーツ,self.ワンピース,self.着物,self.レオタード])


    def get_kaizoudo(self):
        """
        オーバーライド､検索条件の違い

        このget_kaizoudoメソッドは、シーンに応じて解像度をCSVファイルから読み込むために使うんだ。
        TRAINシーンとその他のEVENTシーンで読み取るCSVが異なるから、条件分岐を使って適切なCSVを選択するぜ。

        TRAINシーンの場合はTrain.csvから、その他の場合はEvent.csvから解像度を取得するんだ。
        解像度は、画像生成における品質を決定する重要な要素だから、正確に取得することが大事だぜ！
        """
        # TRAINとその他のEVENTで読み取るcsvが異なる
        from module.sub import get_width_and_height
        if self.scene == "TRAIN":
            tra = self.get_csvname("train")
            kaizoudo = csvm.get_df(tra,"コマンド番号",self.comNo,"解像度")
            if kaizoudo != "ERROR":
                self.width, self.height = get_width_and_height(kaizoudo)

        #これ用のプロンプトや解像度はあとでCSVにかく
        elif self.scene == "マスター移動" or self.scene == "ターゲット切替":
            return

        else:
            eve = self.get_csvname("event")
            kaizoudo = csvm.get_df(eve,"名称",self.scene,"解像度")
            if kaizoudo != "ERROR":
                self.width, self.height = get_width_and_height(kaizoudo)
