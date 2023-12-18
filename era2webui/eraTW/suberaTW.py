from eraTW.cloth import ClothFlags, get_cloth_dict
#from eraTW.emo import Expression
from module.csv_manager import CSVMFactory
from module.sub import get_width_and_height

csvm = CSVMFactory.get_instance()
class PromptMaker:
    """
    このPromptMakerクラスは、eraTWゲームの状況に合わせたプロンプトを作るための強力なツールだぜ。
    シナリオやキャラクターの状態に応じた、細かくカスタマイズされたテキストを生成するんだ。使い方を間違えないようにな！

    Attributes:
        sjh (SaveJSONHandler): ゲームのセーブデータを管理するインスタンス。これがないと始まらないぜ。
        erascene (str): 現在のシーンを格納している。シーンによって生成するプロンプトが変わるから重要だ。
        prompt (dict): シナリオに関連するプロンプトを格納する辞書。ここにデータを詰め込むんだ。
        negative (dict): ネガティブなプロンプトを格納する辞書。時にはダークな面も見せる必要があるからな。
        flags (dict): 描画に関する各種フラグを保持する辞書。どんなシーンを描くかはこれで決まるぜ。
        csv_files (dict): CSVファイルの名前とそれに関連するキーを格納する辞書。データはここから引っ張るんだ。

    Methods:
        generate_prompt: 様々な条件に基づいてプロンプトを生成する。ここがこのクラスの肝だぜ。
        他にもいろいろなメソッドがあるけど、詳細はコードを見てくれ。長くなるからここでは割愛するぜ。

    このクラスを使って、どんなシナリオでも対応できるプロンプトを作り出せるぜ。使いこなせるかな？
    """
    def __init__(self, sjh):
        self.sjh = sjh
        self.erascene = self.sjh.get_save("scene") #sceneは色んなところで読み込むので先に読み込んどく
        self.prompt =    {"situation":"", "location":"", "weather":"","scene":"",\
                          "chara":"","cloth":"","train": "","emotion": "","stain": "",\
                          "潤滑": "","effect": "","eyes": "", "body": "","hair": ""}
        self.negative =  {"situation":"", "location":"", "weather":"","scene":"",\
                          "chara":"","cloth":"", "train": "","emotion": "","stain": "",\
                          "潤滑": "","effect": "","eyes": "", "body": "","hair": ""}
        self.flags = {"drawchara":1,"drawface":1,"drawbreasts":0,\
            "drawvagina":0,"drawanus":0,"主人公以外が相手":0,"indoor":0} #テスト用にキャラと顔は明示的にOFFalseにしないと出る
        self.width = 0
        self.height = 0
        self.csv_files  = {"location":'Location.csv',"weather":'Weather.csv',"cloth":'Cloth.csv',\
                           "train":'Train.csv',"talent":'Talent.csv',"event":'Event.csv',\
                           "equip":'Equip.csv',"chara":'Character.csv',"effect":'Effect.csv',\
                           "emotion":'Emotion.csv'}


    def generate_prompt(self):
        """
        このgenerate_promptメソッドは、elementsをギュッと集めて呪文を生成するんだ。
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
        self.create_situation_prompt()
        self.create_location_prompt()
        #屋内なら天気は無し､昼夜もなしになるのであとで考える
        if self.flags.get("indoor") == 1:
            self.create_weather_prompt()

        #表情ブレンダーはオーバーホールするまで暫定的にここへ
        #p,n = Expression(self.sjh,self.flags)
        #self.add_prompt("emotion", p, n)

        if self.erascene == "TRAIN":
            self.create_train_prompt()
            self.create_effect_prompt()
            if self.flags.get("drawchara") == 1:
                self.create_equip_prompt()
                self.create_chara_prompt()
                self.create_body_prompt()
                #self.clothing()
            self.create_cum_prompt()
            if self.flags.get("drawvagina") ==1:
                self.create_juice_prompt()
        else:
            self.create_chara_prompt()
            self.create_body_prompt()
            self.create_train_prompt()
            #self.clothing()

        #辞書が空の箇所を消す
        prompt_values = [value for value in self.prompt.values() if value.strip()]
        #カンマとスペースを足してヒトツナギに
        prompt = ", ".join(prompt_values)
        negative_values = [value for value in self.negative.values() if value.strip()]
        negative = ", ".join(negative_values)
        width = self.width
        height = self.height
        prompt = csvm.chikan(prompt)
        negative = csvm.chikan(negative)
        self.prompt_debug()
        return prompt,negative,width,height


    def get_csvname(self, key):
        """
        指定されたキーに対応するCSVファイル名を引っ張ってくるメソッドだ。
        必要なファイル名をサクッと探し出すんだぜ。
        Args:
            key (str): CSVファイル名を取得したいキー。ちゃんと正しいキーを渡すんだぜ！

        Returns:
            str: 指定されたキーに対応するCSVファイル名。もしキーがなければ、Noneを返すぜ。
                正しいファイル名を取得できるかどうかは、お前の渡したキー次第だな！
        """
        return self.csv_files.get(key)


    def add_prompt(self, elements, prompt, nega):
        """
        指定された要素に対してプロンプトやネガティブプロンプトを追加するんだ。
        渡したエレメントが辞書に存在しない場合は、このメソッドが手痛いお仕置きをするから気をつけてくれよな！

        Args:
            elements (str): プロンプト要素のキーだ。辞書にあるキーを正しく渡すんだぜ。
            prompt (str): 追加したいプロンプトのテキスト。Noneか'ERROR'じゃなければ追加するぜ。
            nega (str): 追加したいネガティブプロンプトのテキスト。こっちもNoneか'ERROR'じゃなければ追加する。

        Raises:
            KeyError: '{elements}'がプロンプト辞書にないときに投げられる例外だ。ちゃんと辞書を確認してから使ってくれよな！
            KeyError: ネガティブプロンプト辞書に'{elements}'がないときにも同じ例外が飛ぶぜ。こっちも確認しておくんだな！

        このメソッドを使えば、お前の辞書に新しいプロンプトやネガティブプロンプトをサクッと追加できるぜ。
        """
        if elements not in self.prompt:
            raise KeyError(f" '{elements}' なんてプロンプト要素、ないぜ！")
        if elements not in self.negative:
            raise KeyError(f"ネガティブプロンプトに '{elements}' は存在しない！")

        if prompt is not None and prompt != "ERROR":
            self.prompt[elements] += prompt
        if nega is not None and nega != "ERROR":
            self.negative[elements] += nega


    def update(self):
        """
        このupdateメソッドは、現在のゲーム状況に合わせてコマンド名を更新するために使うんだ。
        特に、キャラクターの特徴や状況に応じてコマンドを差し替える処理を行う。

        例えば、巨乳未満のキャラで'パイズリ'コマンドが使われた場合、それを'ナイズリ'に変更する。
        また、着衣時の胸愛撫は別のコマンドに変える処理もあるぜ。

        このメソッドは、SaveJSONHandlerのデータを適切に更新することで、シナリオのリアリティを高める役割を果たす。
        """
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
        """
        このcreate_situation_promptメソッドは、現在のシナリオに合わせて状況のプロンプトを生成するんだ。
        特に、ターゲットの切り替えやマスターの移動などのシーンに応じて、適切なプロンプトを組み立てるぜ。

        基礎プロンプトのネガティブプロンプトは常に追加される。
        さらに、シナリオがターゲット切替やマスター移動の場合、
        特定の条件に基づいて異なるプロンプトを追加する。
        """
        efc = self.get_csvname("effect")
        #何はなくとも基礎プロンプトのネガティブ入れる
        nega = csvm.get_df(efc,"名称","基礎プロンプト","ネガティブ")
        self.add_prompt("situation", None, nega)
        if self.erascene == "ターゲット切替" or \
            self.erascene == "マスター移動":

            if self.sjh.get_save("キャラ固有番号") == 0:
                self.add_prompt("situation", "(empty scene)", "(1girl:1.5)")
            else:
                self.add_prompt("situation", "1girl standing, detailed scenery in the background", None)
                self.flags["drawchara"] = 1
                self.flags["drawface"] = 1


    def create_location_prompt(self):
        """
        現在のシナリオに合わせて、ロケーションに関するプロンプトを生成するメソッドだぜ。
        CSVファイルからロケーションに関するデータを読み込み、適切なプロンプトとネガティブプロンプトを追加する。

        ロケーションが屋内か屋外かもチェックして、フラグを設定するんだ。この情報は天気のプロンプトを生成するときにも使われるぜ。
        """
        # 700箇所
        #IDとの整合はあとで確かめる
        master = self.sjh.get_save("現在位置")
        loc = self.get_csvname("location")
        prompt = csvm.get_df(loc,"地名", master,"プロンプト")
        nega = csvm.get_df(loc,"地名", master,"ネガティブ")
        self.add_prompt("location", prompt, nega)
        #室内外かはCSVに書いて
        doors = csvm.get_df(loc,"地名", master,"室内外")
        if doors == "indoor":
            self.flags["indoor"] = 1
        self.add_prompt("location", doors, None)


    def create_weather_prompt(self):
        """
        現在の天気に応じて、天気のプロンプトを生成するメソッドだぜ。
        CSVファイルから天気データを読み込んで、適切なプロンプトとネガティブプロンプトを組み立てる。

        さらに、時間に基づいて昼か夜かの情報をプロンプトに追加する。これで、シナリオのリアリティがさらに高まるぜ！

        """
        天気 = self.sjh.get_save("天気")
        wea = self.get_csvname("weather")
        prompt = csvm.get_df(wea,"天気", 天気,"プロンプト")
        nega = csvm.get_df(wea,"天気", 天気,"ネガティブ")

        if prompt != "ERROR":
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
        """
        このcreate_train_promptメソッドは、調教シーンのためのプロンプトを生成するんだ。
        CSVファイルから読み込んだコマンド名に基づいて、適切なプロンプトとネガティブプロンプトを組み立てるぜ。

        調教が成功したか失敗したかによって処理が分岐するから、それもしっかりチェックしてくれよな。
        成功した場合は、CSVから読み込んだ情報に基づいてプロンプトを作成する。失敗した場合は、拒否プロンプトを使うんだ。

        このメソッドを使えば、どんなトレーニングシーンにもぴったりなプロンプトを作り出せるぜ！
        """
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
                prompt = csvm.get_df(eve,"名称","汎用調教","プロンプト")
                nega = csvm.get_df(eve,"名称","汎用調教","ネガティブ")

                self.flags["drawchara"] = csvm.get_df(eve,"名称","汎用調教","キャラ描画")
                self.flags["drawface"] = csvm.get_df(eve,"名称","汎用調教","顔描画")
                self.flags["drawbreasts"] = csvm.get_df(eve,"名称","汎用調教","胸描画")
                self.flags["drawvagina"] = csvm.get_df(eve,"名称","汎用調教","ヴァギナ描画")
                self.flags["drawanus"] = csvm.get_df(eve,"名称","汎用調教","アナル描画")

                self.add_prompt("train", prompt, nega)
            nega = csvm.get_df(tra,"コマンド名",com,"ネガティブ")
            self.add_prompt("train", prompt, nega)


    def create_equip_prompt(self):
        """
        このcreate_equip_promptメソッドは、現在のゲーム状況に合わせて装備品のプロンプトを生成するんだ。
        CSVファイルから装備品に関するデータを読み込み、適切なプロンプトとネガティブプロンプトを追加するぜ。

        装備品は、シーンの構図によって表示されるかどうかが変わる。
        だから、描画フラグに基づいて装備品をスキップする処理も行うんだ。
        こうすることで、シナリオのリアリティを高めることができるぜ！
        """
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
        """
        このcreate_stain_promptメソッドは、特定の条件下での精液の付着を描写するプロンプトを生成するために使うんだ。
        キャラクターの描画フラグに基づいて、適切なプロンプトを組み立てるぜ。

        たとえば、キャラクターが描画される場合には、装備品のプロンプトも考慮に入れるんだ。
        さらに、胸やヴァギナに精液が付着しているかどうかをチェックして、それに応じたプロンプトを追加する。
        """
        # 付着した精液
        #装備 調教対象キャラが映るときのみ
        #これは別モジュールに移したほうがいいかも
        if self.flags["drawchara"] == 1:
            self.create_equip_prompt()

        if self.flags["drawbreasts"] == 1:
            if (self.sjh.get_save("胸の汚れ") & 4)  == 4:
                self.add_prompt("stain", "(cum on breasts)", None)
        if self.flags["drawvagina"] == 1:
            if (self.sjh.get_save("膣内射精フラグ")) >= 1:
                self.add_prompt("stain", "cum drip from pussy", None)

        # cum on ～ はちんちんを誘発、semen on ～ はほとんど効果がない
        # milkはときどきグラスが出る


    def create_chara_prompt(self):
        """
        このcreate_chara_promptメソッドは、キャラクターの描画に関するプロンプトを生成するために使うんだ。
        CSVファイルからキャラクターに関するデータを読み込み、適切なプロンプトとネガティブプロンプトを追加するぜ。

        毎回記述されるキャラクターの基本的なプロンプトはEffect.csvから読み出す。
        さらに、特別な名前でプロンプトを登録してある場合は、キャラクター描写を強制的に上書きする処理も行うんだ。

        """
        cha = self.get_csvname("chara")
        efc = self.get_csvname("effect")

        # キャラ描写で毎回記述するプロンプト Effect.csvから読み出す
        charabase = csvm.get_df(efc,"名称","人物プロンプト","プロンプト")
        charabase = charabase + ", " #charaキーで辞書に格納する時カンマ スペースが入らないのでここで足す
        self.add_prompt("chara", charabase, None)

        # 特別な名前でプロンプトを登録してある場合、キャラ描写を強制的に上書きする処理
        uwagaki = csvm.get_df(cha,"キャラ名","描画キャラ上書き","プロンプト")
        if uwagaki != "ERROR": #EROORじゃなかったら上書き
            prompt = f"({uwagaki})"
            nega = csvm.get_df(cha,"キャラ名","描画キャラ上書き","ネガティブ")
            self.add_prompt("chara", prompt, nega)

        else:
            #割り込みがなければ通常のキャラプロンプト読み込み処理
            name = self.sjh.get_save("target")
            prompt = csvm.get_df(cha,"キャラ名",name,"プロンプト")
            prompt_wait = csvm.get_df(cha,"キャラ名",name,"プロンプト強調")
            # prompt_waitが"ERROR"でない場合にのみ結合する
            if prompt_wait != "ERROR":
                prompt = f"({prompt}:{prompt_wait})"
            self.add_prompt("chara", prompt, None)

            prompt2 = csvm.get_df(cha,"キャラ名",name,"プロンプト2")
            self.add_prompt("chara", prompt2, None)

            chara_lora = csvm.get_df(cha,"キャラ名",name,"キャラLora")
            nega = csvm.get_df(cha,"キャラ名",name,"ネガティブ")
            self.add_prompt("chara", chara_lora, nega)


    def create_cum_prompt(self):
        """
        このcreate_cum_promptメソッドは、射精箇所に基づいてプロンプトを生成するために使うんだ。
        ビット演算を使って、どの射精箇所が選ばれているかを判定するぜ。

        ビット演算ってのは、数字をビット単位で見て、特定のビットが立っているかどうかをチェックする方法だ。
        たとえば、'射精箇所'がビットで示されていて、各ビットが特定の射精箇所を表しているんだ。
        """
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
        """
        このcreate_juice_promptメソッドは、キャラクターの潤滑状態に基づいてプロンプトを生成するんだ。
        TRAINシーン限定で、ヴァギナ描画がonのときに使われるぜ。

        潤滑度の値に基づいて、適切なプロンプトを追加するんだ。
        たとえば、潤滑度が低い場合は特定のネガティブプロンプトを、潤滑度が高い場合はより具体的なプロンプトを追加する。
        """
        #TRAIN限定のエフェクト
        # ヴァギナ描画onのとき
        if self.flags["drawvagina"] == 1: #判定は別のメソッドに回す あとで
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
        """
        このcreate_traineffect_promptメソッドは、TRAINシーン限定の特定エフェクトに基づいてプロンプトを生成するために使うんだ。
        CSVファイルからエフェクトに関するデータを読み込み、適切なプロンプトを追加するぜ。

        破瓜の血や放尿など、特定の状況で発生するエフェクトを考慮に入れて、シナリオのリアリティを高めるプロンプトを作成するんだ。
        """
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
        """
        このcreate_effect_promptメソッドは、キャラクターの特定の状態や状況に基づいてプロンプトを生成するんだ。
        CSVファイルからエフェクトに関するデータを読み込み、適切なプロンプトを追加するぜ。

        たとえば、キャラクターが妊娠している場合、妊娠の進行度に応じて異なるプロンプトを追加するんだ。
        これによって、シナリオのリアリティがさらに高まるぜ！
        """
        efc = self.get_csvname("effect")
        if "妊娠" in self.sjh.get_save("talent"):
            # 標準で20日で出産する。残14日から描写し、残8日でさらに進行
            if self.sjh.get_save("出産日") - self.sjh.get_save("日付") in range(8,14):
                prompt = csvm.get_df(efc,"名称","妊娠中期","プロンプト")
            elif (self.sjh.get_save("出産日") - self.sjh.get_save("日付")) <= 8:
                prompt = csvm.get_df(efc,"名称","妊娠後期","プロンプト")
                self.add_prompt("effect", prompt, None)


    def create_eyes_prompt(self):
        """
        このcreate_eyes_promptメソッドは、キャラクターの目の色に基づいてプロンプトを生成するんだ。
        CSVファイルからキャラクターの目の色に関するデータを読み込み、適切なプロンプトを追加するぜ。

        キャラクターの目の色は、そのキャラクターの個性や雰囲気を伝える重要な要素だから、しっかりと反映させるんだ。
        """
        #目の色をクラス辞書に追記しておく
        cha = self.get_csvname("chara")
        prompt = csvm.get_df(cha,"キャラ名",self.sjh.get_save("target"),"目の色")
        self.add_prompt("chara", prompt, None)



    def create_body_prompt(self):
        """
        このcreate_body_promptメソッドは、キャラクターの体の特徴に基づいてプロンプトを生成するために使うんだ。
        CSVファイルから体の特徴に関するデータを読み込み、適切なプロンプトを追加するぜ。

        乳サイズや体格、体型など、キャラクターの特徴をしっかりと表現するプロンプトを組み立てるんだ。
        特に、普通の乳サイズなのに誤って巨乳と描写されることを避けるための工夫もしているぜ！

        このメソッドを使えば、キャラクターの体の特徴を効果的に表現できるぜ！
        """
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
                    nega += "areolae, nipple" #negaが空白だった時用対策
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
        """
        このcreate_hair_promptメソッドは、キャラクターの髪型に基づいてプロンプトを生成するために使うんだ。
        CSVファイルから髪型に関するデータを読み込み、適切なプロンプトを追加するぜ。

        長髪、セミロング、ショートカット、ツインテールなど、さまざまな髪型を考慮に入れる。
        髪型はキャラクターの個性を表現するのに重要な要素だから、しっかりと反映させるんだ。
        """
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
        """
        あとでアスペクト比を基に可変できるようにする
        このget_kaizoudoメソッドは、シーンに応じて解像度をCSVファイルから読み込むために使うんだ。
        TRAINシーンとその他のEVENTシーンで読み取るCSVが異なるから、条件分岐を使って適切なCSVを選択するぜ。

        TRAINシーンの場合はTrain.csvから、その他のEVENTシーンの場合はEvent.csvから解像度を取得するんだ。
        解像度は、画像生成における品質を決定する重要な要素だから、正確に取得することが大事だぜ！
        """
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
        """
        このclothingメソッドは、キャラクターの装備や服装に基づいてプロンプトを生成するために使うんだ。
        CSVファイルから服装に関するデータを読み込み、適切なプロンプトを追加するぜ。

        ノーパンやノーブラの判定、露出状態の判定も行う。服装はシナリオの雰囲気やキャラクターの個性を伝える重要な要素だから、しっかりと反映させるんだ。

        注意：このメソッドはまだ未完成だ。いつか完成させるぜ！
        """
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
            for key, value in cloth_dict.items():
                if key in clothings:
                    prompt = csvm.get_df(clo,"衣類名", value, "プロンプト")
                    if prompt != "ERROR":
                        prompt = f"(wearing {prompt}:1.3)"
                        nega = csvm.get_df(clo,"衣類名", value, "ネガティブ")
                        self.add_prompt("cloth", prompt, nega)

        # 下半身上着
        if (pantse == 0 and pussye == 0)\
            or self.sjh.get_save("下半身ずらし状態") == 1:
            clothings = ["下半身上着1","下半身上着2","スカート", "ズボン",]
            for key, value in cloth_dict.items():
                if key in clothings:
                    prompt = csvm.get_df(clo,"衣類名", value, "プロンプト")
                    if prompt != "ERROR":
                        prompt = f"(wearing {prompt}:1.3)"
                        nega = csvm.get_df(clo,"衣類名", value, "ネガティブ")
                        self.add_prompt("cloth", prompt, nega)

        for key, value in cloth_dict.items():
            clothings = ["帽子", "アクセサリ", "腕部装束", "外衣", "上半身下着2",\
                         "下半身下着1", "その他1", "その他2", "その他3", "靴下", "靴"]
            if key in clothings:
                prompt = csvm.get_df(clo,"衣類名", value, "プロンプト")
                nega = csvm.get_df(clo,"衣類名", value, "ネガティブ")
                self.add_prompt("cloth", prompt, nega)

        if nob: #ノーブラ
            prompt = csvm.get_df(clo,"衣類名","ノーブラ","プロンプト")
            nega = csvm.get_df(clo,"衣類名","ノーブラ","ネガティブ")
            self.add_prompt("cloth", prompt, nega)

        elif burae == 1: #ブラ見える
            if self.sjh.get_save("上半身下着2") != 0:
                prompt = csvm.get_df(clo,"衣類名",self.sjh.get_save("upper_underwear"),"プロンプト")
                if prompt != "ERROR":
                    prompt = f"(wearing {prompt}:1.3)"
                    nega = csvm.get_df(clo,"衣類名", value, "ネガティブ")
                    self.add_prompt("cloth", prompt, nega)

        if nop: #ノーパン
            prompt = csvm.get_df(clo,"衣類名","ノーパン","プロンプト")
            nega = csvm.get_df(clo,"衣類名","ノーブラ","ネガティブ")
            self.add_prompt("cloth", prompt, nega)
        elif burae == 1: #パンツ見える
            if self.sjh.get_save("上半身下着2") != 0:
                prompt = csvm.get_df(clo,"衣類名",self.sjh.get_save("upper_underwear"),"プロンプト")
                if prompt != "ERROR":
                    prompt = f"(wearing {prompt}:1.3)"
                    nega = csvm.get_df(clo,"衣類名", value, "ネガティブ")
                    self.add_prompt("cloth", prompt, nega)

        # panty aside
        # 挿入とクンニ
        if (self.sjh.get_save("マスターがＶ挿入") != 0 )\
            or(self.sjh.get_save("マスターがＡ挿入") != 0)\
            or (self.sjh.get_save("コマンド") == "1"):
            if self.sjh.get_save("下半身下着2") != 0:
                self.add_prompt("cloth", "(pantie aside)", None)


    def prompt_debug(self):
        """
        生成前にどんな要素を格納されてるか調べるやつ
        """
        for key, value in self.prompt.items():
            print (f'prompt:::{key}:::{value}')
        for key, value in self.negative.items():
            print (f'nega:::{key}:::{value}')
        for key, value in self.flags.items():
            print (f'flags:::{key}:::{value}')




    #あとで emomoduleのオーバーホール     #表情ブレンダー
    