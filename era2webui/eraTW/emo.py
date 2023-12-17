import random
import numpy as np
from eraTW.suberaTW import PromptMaker
from module.csv_manager import CSVMFactory
csvm = CSVMFactory.get_instance()

# cgpro用の表情コード
# 暫定でバリアント毎に分けたけど更新が面倒になるのでホントはまとめたい
# YM用の記述や未対応部分はコメントアウト


# 表情ブレンダー
# 表情のプロンプトは実行中に弄りたいのでいつかcsv化する

# 様々な表情の単語をブレンドしても良い顔ができない上に構図や絵柄に深刻な悪影響があることがわかった。
# 要素ごとにプロンプトを追加していくやり方ではすぐ限界が来る。


class Expression(PromptMaker):
    def __init__(self, sjh):
        super().__init__(sjh)
        self.emoflags = {"ClosedEyes":False,"NotMaster":False,"drawbreasts":False,\
                      "drawvagina":False,"drawanus":False,"強い情動":False,"苦痛":False}
        self.emolevel = {"快感Lv":0,"睡眠深度":0,"体力Lv":0,"気力Lv":0,"酩酊Lv":0,"苦痛Lv":0,"恐怖Lv":0}
        self.emo = self.get_csvname("emotion")
    # eyeprompt = ""  # 目の処理はeyepromtに書き溜め、後で結合するが、最終的にclosed eyesフラグが立ってれば削除
    # Pain = False
    # tsuyoijoudou = False
    # Love = False



    def emotionflags(self):
        # TEQUIP:18 アイマスク (cgpro)
        if "18" in self.sjh.get_save("equip"):
            self.emoflags["ClosedEyes"] = True


        if self.sjh.get_save("scene") == "TRAIN":
            if self.sjh.get_save("PLAYER") != 0:
                self.emoflags["NotMaster"] = True
                print("助手とか")
        else:
            if self.flags["主人以外が相手"] == 1:
                self.emoflags["NotMaster"] = True
                print("主人以外が相手のイベント")

    def check_pleasure_level(self):
        pleasure = self.sjh.get_save("palam_up")["快Ｃ"]\
                  +self.sjh.get_save("palam_up")["快Ｂ"]\
                  +self.sjh.get_save("palam_up")["快Ｖ"]\
                  +self.sjh.get_save("palam_up")["快Ａ"]
        if pleasure >= 7500:
            self.emolevel["快感Lv"] = 4
            self.emoflags["強い情動"] = True
            self.add_prompt("eyes", "{rolling eyes|}", None)
        elif pleasure >= 3000:
            self.emolevel["快感Lv"] = 3
            self.emoflags["強い情動"] = True
        elif pleasure >= 1000:
            self.emolevel["快感Lv"] = 2
            self.emoflags["強い情動"] = True
        elif pleasure >= 1000:
            self.emolevel["快感Lv"] = 1
            self.emoflags["強い情動"] = True

    def check_hp_level(self):
        max_hp = self.sjh.get_save("最大体力")
        current_hp = self.sjh.get_save("体力")
        hp_ratio = current_hp / max_hp

        if current_hp <= 0:
            self.emolevel["体力Lv"] = 0  # 死亡（レベル5）
        elif hp_ratio <= 0.2:
            self.emolevel["体力Lv"] = 1  # 非常に低い体力
        elif hp_ratio <= 0.4:
            self.emolevel["体力Lv"] = 2  # 低い体力
        elif hp_ratio <= 0.6:
            self.emolevel["体力Lv"] = 3  # 中程度の体力
        elif hp_ratio <= 0.8:
            self.emolevel["体力Lv"] = 4  # 高い体力
        else:
            self.emolevel["体力Lv"] = 5  # 非常に高い体力（フル）


    def check_drunk_level(self):
        drunk_value = self.sjh.get_save("酔い")

        if drunk_value >= 10000:
            self.emolevel["酩酊Lv"] = 5
        elif drunk_value >= 6000:
            self.emolevel["酩酊Lv"] = 4
        elif drunk_value >= 3000:
            self.emolevel["酩酊Lv"] = 3
        elif drunk_value >= 1000:
            self.emolevel["酩酊Lv"] = 2
        elif drunk_value >= 1000:
            self.emolevel["酩酊Lv"] = 1


    def check_pain_level(self):
        pain_value = self.sjh.get_save("palam_up")["苦痛"]

        if pain_value > 3000:
            self.emolevel["苦痛Lv"] = 2  # 重い苦痛
        elif pain_value > 500:
            self.emolevel["苦痛Lv"] = 1  # 軽い苦痛


    def check_fear_level(self):
        fear_value = self.sjh.get_save("palam_up")["恐怖"]

        if fear_value > 10000:
            self.emolevel["恐怖Lv"] = 5  # 極度の恐怖
        elif fear_value >= 6000:
            self.emolevel["恐怖Lv"] = 4  # 非常に強い恐怖
        elif fear_value >= 3000:
            self.emolevel["恐怖Lv"] = 3  # 強い恐怖
        elif fear_value >= 1000:
            self.emolevel["恐怖Lv"] = 2  # 明確な恐怖
        elif fear_value > 300:
            self.emolevel["恐怖Lv"] = 1  # 軽い恐怖


    # def check_mp_level(self):
        #if self.sjh.get_save("気力") < 100:


    def create_sleep_prompt(self):
        #148,睡眠薬強度
        #(0=通常睡眠　1=深い睡眠　2=非常に深い睡眠　3=昏睡)
        #TCVAR:TARGET:睡眠深度  あとでTEXTLOG.ERBを書き換える
        #睡眠深度のあとでemolvelにまとる
        emo = self.emo
        if (self.sjh.get_save("睡眠薬") > 0) or (self.sjh.get_save("失神") >= 2):
            睡眠深度 = self.sjh.get_save("睡眠深度")
            prompt = csvm.get_df(emo,"名前", 睡眠深度,"プロンプト")
            nega = csvm.get_df(emo,"名前", 睡眠深度,"ネガティブ")
            self.emoflags["ClosedEyes"] = True
            self.add_prompt("emotion", prompt, nega)
            # 暫定で表情変化なしにする。
            self.flags["drawface"] = 0
            # でも欲情と絶頂はちょっと効くように
            self.check_pleasure_level()  # 快感レベルをチェック
            pleasure_level = self.emolevel.get("快感Lv")
            prompt = csvm.get_df_2key(emo, "状態", "快感Lv", "level", pleasure_level, "プロンプト")
            self.add_prompt("emotion", prompt, None)
            if self.sjh.get_save("絶頂の強度") > 0:
                self.add_prompt("emotion", "(motion lines:1.2),(blush:0.9)", None)


    def create_hp_prompt(self):
        emo = self.emo
        self.check_hp_level()
        hp_level = self.emoflags("体力Lv")
        prompt = csvm.get_df_2key(emo, "状態", "体力Lv", "level", hp_level, "プロンプト")
        self.add_prompt("emotion", prompt, None)
        if hp_level == 1:
            # 瀕死状態のプロンプトを追加
            eyeprompt = "(half closed eyes,empty eyes:1.5)"
            self.add_prompt("eyes", eyeprompt, None)

    def create_mp_prompt(self):
        emo = self.emo
        prompt = csvm.get_df_2key(emo, "状態", "気力Lv", "level", 1, "プロンプト")
        self.add_prompt("emotion", prompt, None)
        self.emoflags["強い情動"] = True


    def create_drunk_prompt(self):
        emo = self.emo
        drunk_level = self.check_drunk_level()
        prompt = csvm.get_df_2key(emo, "状態", "酩酊Lv", "level", drunk_level, "プロンプト")
        self.add_prompt("eyes", prompt, None)


    def create_pain_prompt(self):
        emo = self.emo
        pain_level = self.check_pain_level()
        pain_level = self.emolevel.get("苦痛Lv")

        if pain_level >= 2:
            self.emoflags["強い情動"] = True
            self.emoflags["苦痛"] = True
            # 重い苦痛の追加プロンプト
            ra = random.randrange(2)
            if ra == 0: #目と口をギュッと閉じるパターン
                prompt = csvm.get_df_2key(emo, "状態", "苦痛Lv", "level", 2, "プロンプト")
                nega = csvm.get_df_2key(emo, "状態", "苦痛Lv", "level", 2, "ネガティブ")
                self.emoflags["ClosedEyes"] = True
                self.add_prompt("emotion", prompt, nega)
            elif ra == 1: #目を見開くパターン
                prompt = csvm.get_df_2key(emo, "状態", "苦痛Lv", "level", 3, "プロンプト")
                nega = csvm.get_df_2key(emo, "状態", "苦痛Lv", "level", 3, "ネガティブ")
                self.add_prompt("emotion", prompt, nega)
                self.add_prompt("eyes", "(startled eyes,.-.),", "smile")
        elif pain_level == 1:
            prompt = csvm.get_df_2key(emo, "状態", "苦痛Lv", "level", pain_level, "プロンプト")
            self.add_prompt("emotion", prompt, None)


    def create_fear_prompt(self):
        emo = self.emo
        self.check_fear_level()
        fear_level = self.emolevel.get("恐怖Lv")
        prompt = csvm.get_df_2key(emo, "状態", "恐怖Lv", "level", fear_level, "プロンプト")

        self.add_prompt("eyes", "(startled eyes,.-.),", "smile")



    # # 顔を見せない構図なら表情作りはスキップ
    # if flags["drawface"] == 1 :
        #あとでプロンプトを束ねるときに使う
    #気力がないとぐったりする
        #if self.sjh.get_save("気力") < 100:
# 調教に対する反応 TRAIN中のみ反映＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊
#        if self.sjh.get_save("scene") == "TRAIN":
             # # 刻印レベルの苦痛フラグが立ってる場合、好意・欲望・羞恥の表情をつけない。ただし高レベルマゾは例外
            # if (Pain == False) or (self.sjh.get_save("abl")["マゾっ気"] >= 4):
                # 欲情の判定-----------------------------------------------------------------

        ahe_strength = self.sjh.get_save("快楽強度")

        # 淫乱持ちは少しアヘりやすい
        # 恋慕と排他じゃないバリアントでは望まなくても淫乱がついてしまうので控えめの補正にする
        if "淫乱" in self.sjh.get_save("talent"):
            if ahe_strength > 0:
                ahe_strength += 2
        # 四重絶頂で補正
        tajuu = np.count_nonzero([self.sjh.get_save("Ｃ絶頂"),self.sjh.get_save("Ｂ絶頂"),self.sjh.get_save("Ｖ絶頂"),self.sjh.get_save("Ａ絶頂")])
        if tajuu == 4:
            ahe_strength += 6

        # 基本の絶頂エフェクト
        if ahe_strength > 0:
            prompt += "(motion lines:1.2),"
            eyeprompt += "(startled eyes),"

        if ahe_strength >= 4: #強度4　2重強絶頂以上でアヘり始める
            #絶頂強度4～7 軽めのアヘ顔
            if ahe_strength <= 7:
                prompt += "(ahegao:0.7),"
            #絶頂強度8～11 そこそこアヘ顔 最強絶頂で9 淫乱なら11に届く。単発Vセックスとかでこれ以上に届いてほしくはない
            elif ahe_strength <= 11:
                prompt += "ahegao,{open mouth|:o},drooling,saliva,"
            #絶頂強度12～14 だいぶアヘ顔
            elif ahe_strength <= 14:
                prompt += "<lora:ahegao_v1:0.8:1:lbw=F>,ahegao,open mouth,drooling,saliva,"
            #絶頂強度14～16 かなりアヘ顔 
            elif ahe_strength <= 16:
            #確率でheadback 20%
            #headbackは表情描写と衝突して絵が壊れるっぽい
                ra = random.randrange(4)
                if ra == 0:
                    prompt += "<lora:conceptHeadbackArched_v10:1:CT>,(HEADBACK) "
                    ClosedEyes = True
                else:
                    prompt += "<lora:ahegao_v1:1.5:1:lbw=F>,(ahegao),open mouth,drooling,saliva,"
            #絶頂強度17超え 完全にアヘ顔 
            else:
                prompt += "<lora:ahegao_v1:1.6:1:lbw=F>,(ahegao:1.5),open mouth,(drooling),saliva,"

                # 羞恥の判定-----------------------------------------------------------------

                # embarrassed 1.2でもう十分なくらい恥ずかしそう blushが1.0ついている場合0.5位まで変化なし
                # 普通の調教だと恥情はあんまり上がらないが欲情で赤くなってるはず
                # embarrassedよりshameの方がマイルド なはず
                if self.sjh.get_save("palam")["恥情"] >= 1000:
                    if self.sjh.get_save("palam")["恥情"] <= 5000:
                        prompt += "(shame:0.5),"
                    elif self.sjh.get_save("palam")["恥情"] <= 10000:
                        prompt += "(shame:0.7),"
                    else:
                        prompt += "shame,"
                if self.sjh.get_save("palam_up")["恥情"] >= 500:

                    if self.sjh.get_save("palam_up")["恥情"] < 1000:
                        prompt += "(embarrassed:0.6),"
                    else:
                        tsuyoijoudou = True
                        prompt += "embarrassed,"

        # ここからは素質・刻印等によるもの TRAIN以外でも反映＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊

        # 反発 の判定-----------------------------------------------------------------
        # angerは口が歪んだりギャグみたいになる
        # Hostileはたまに幼い輪郭になる
        # furiousはへの字口が気になる
        # いずれも反発刻印3に見合うほどの憎悪は感じない

        # 反発刻印と恋慕の効果は主人以外には向けない
        if NotMaster == False:
            # 反発刻印3
            if self.sjh.get_save("mark")["反発刻印"] == 3:
                prompt += "(Hostile:1.2)," # とりあえず埋めたけど弱い
            # 反発刻印2 重複させる
            if self.sjh.get_save("mark")["反発刻印"] >= 2:
                prompt += "anger," # わかりやすくキレる 軽めにかけないとギャグ顔になる
            
            # 反発刻印1
            if self.sjh.get_save("mark")["反発刻印"] >= 1:
                if not ClosedEyes :
                    eyeprompt += "(glaring eyes:1.0),"
                    tsuyoijoudou = True

            # 従順1がつくまでは嫌われてると判断
            elif self.sjh.get_save("abl")["従順"] == 0:
                if "サド" in self.sjh.get_save("talent"): #frownは困り顔になって一部キャラに違和感があったので
                    prompt += "unamused,"
                else:
                    prompt += "(frown:0.9),"


            # 好意
            # 刻印レベルの苦痛フラグが立ってる場合、好意・欲望・羞恥の表情をつけない。ただし高レベルマゾは例外
            if (Pain == False) or (self.sjh.get_save("abl")["マゾっ気"] >= 4):  
                # 恋慕でハートを盛る
                chk_list = ["恋慕","親愛","相愛"]
                and_list = set(self.sjh.get_save('talent')) & set(chk_list)
                if (len(and_list)) > 0:
                    prompt += "(tender,Loving),(hearts around face:0.8)," # この辺の表情をもっとうまいことやりたい
                    if self.sjh.get_save("palam_up")["恭順"] in range (5000,15000): # ハート増量
                        prompt += "hearts in speech bubble around face,happy,"
                    elif self.sjh.get_save("palam_up")["恭順"] > 15000: # 追加
                        prompt += "(big hearts in speech bubble around face),(happy:1.2),"
                    
                    Love = True


        # 調教初期の表情 つまんなそうな顔
        # 何も指定しないとカワイイ笑顔になるのを防ぐためのデフォルト表情
        # scgpro 初対面シチュエーションが多いので軽めに200で解除する

        taikutsu = 2
        if (self.sjh.get_save("abl")["従順"] > 3) or (self.sjh.get_save("好感度") > 50):
            taikutsu -= 1
        if (self.sjh.get_save("abl")["従順"] > 4) or (self.sjh.get_save("好感度") > 200):
            taikutsu -= 1

        # 性格等で増減

        if tsuyoijoudou == True: # 余裕ないときには退屈な表情はしない
            taikutsu = 0

        if taikutsu >= 2:
            # 従順低い時のサドは挑戦的な顔
            if "サド" in self.sjh.get_save('talent'):
                prompt += "arrogance,"
            else:
                # サド以外は退屈な顔
                prompt += "(Blank expression,boring:1.3),"
        elif taikutsu == 1:
            if "サド" in self.sjh.get_save('talent'):
                prompt += "arrogance,"
            else:
                prompt += "Blank expression,boring,"


        # 強い情動がないとき恋慕でたまに見せる表情
        # ここを性格で個性分けしたい
        if tsuyoijoudou == False:
            if Love == True:
                ra = random.randrange(20)
                if ra == 1:
                    prompt += "(closed eyes smile,blushing:1.3),"
                    ClosedEyes == True
                if ra == 2:
                    prompt += "(closed eyes smile,blushing:1.3),open mouth,"
                    ClosedEyes == True
                if ra == 3:
                    prompt += "(heart racing,blushing:1.3),"
                if ra == 4:
                    prompt += "(delighted),"


        #生来のTalentによる顔つき

        #たれ目傾向 taremeは効きが悪い 恐怖の珠が上がるのでそっちでも補正できる
        chk_list = ["臆病","大人しい","悲観的"]
        and_list = set(self.sjh.get_save('talent')) & set(chk_list)
        if (len(and_list)) > 0:
            prompt += "(tareme),"
            negative += "(glaring:0.7),"

        #ツリ目傾向
        chk_list = ["反抗的","気丈","プライド高い","ツンデレ","サド"]
        and_list = set(self.sjh.get_save('talent')) & set(chk_list)
        if (len(and_list)) > 0:
            eyeprompt += "(glaring eyes:0.7)," # 0.7でもよく効いたり全然効かなかったりする。


        #無感情 expressionlessは口を閉じる効果が高い。八の字眉傾向
        # empty eyes 
        # chk_list = ["無関心","感情乏しい","抑圧"]
        # and_list = set(self.sjh.get_save('talent')) & set(chk_list)
        # if (len(and_list)) > 0:
        #     if self.sjh.get_save("絶頂の強度") == 0:
        #         eyeprompt += "(empty eyes),"
        #         prompt += "expressionless,"
        #         negative += "((blush)),troubled eyebrows,"


        #狂気 強調しないと滅多に光らないはず。キレたときとか条件付きで光るようにした方がいいかも。した。
        chk_list = ["狂気","狂気の目"]
        and_list = set(self.sjh.get_save('talent')) & set(chk_list)
        if (len(and_list)) > 0:
            if self.sjh.get_save("mark")["反発刻印"] == 3: #反発3だとずっと光る
                eyeprompt += "(glowing eyes:1.4),"
            elif self.sjh.get_save("palam_up")["反感"] >= 500: #反感の上がるようなことをすると光る
                eyeprompt += "(glowing eyes:1.4),"
            else:
                eyeprompt += "glowing eyes," #きまぐれに光る？

        #笑顔up 常に効いてるのはおかしいのでいったん保留
        # chk_list = ["楽観的","解放","鼓舞"]
        # and_list = set(self.sjh.get_save('talent']) & set(chk_list)
        # if (len(and_list)) > 0:
        #     if Pain == False:
        #         prompt += "joyful,"

        #魅力
        chk_list = ["魅力","魅惑","謎の魅力"]
        and_list = set(self.sjh.get_save('talent')) & set(chk_list)
        if (len(and_list)) > 0:
            prompt += "seductive,"

        #頭よさそう
        chk_list = ["自制心","快感の否定","教育者","調合知識"]
        and_list = set(self.sjh.get_save('talent')) & set(chk_list)
        if (len(and_list)) > 0:
            prompt += "smart,"

        #ドヤ顔
        chk_list = ["生意気","目立ちたがり"]
        and_list = set(self.sjh.get_save('talent')) & set(chk_list)
        if (len(and_list)) > 0:
            prompt += "(smug:0.6)," #ちょっと強いワード

        #目の処理 Closedでなければeyepromptを統合、csvの目の色を反映
        #eraTWには必要ない処理
        #目の色を表すeraTWの変数は後で探す
        if ClosedEyes == False:
            prompt += eyeprompt
            if self.sjh.get_save("eyecolor"):
                prompt += self.sjh.get_save("eyecolor") + " eyes,"

    # 顔はここまで------------------------------------------------------------------------

    return prompt,negative

