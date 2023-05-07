# era2webuitest

注意：このプログラムはド素人が試作した人柱版です。まともに動作することを期待しないで下さい。
何があっても自己責任での試用をお願いします。
動作にはStable Diffusionによる画像生成環境が必要です。

### なにこれ
eraで遊ぶとプレイ内容をリアルタイムで画像生成する仕組み

### 動作の概要
・emueraのSAVETEXT関数によりプレイ状況をtxtファイルに書き出す

・プログラムがtxtを検知してプロンプト文字列を作り、Stable Diffusionに渡す

（Automatic1111の入力欄にブラウザ自動操作で文字記入する形でやっています。将来的にAPI利用も検討中）

### 動かしかた
1. PCにインストールされたchromeと同バージョンのchromedriverを入手し、本体と同じフォルダに入れる。
2. 同梱のERBフォルダをeraのフォルダに上書きする。
2. -remote-debugging-port=9222オプションをつけてchromeを起動し、WebUIを開いておく。（バッチファイル同梱）
3. era2webui.pyを実行する。（バッチファイル同梱）


### カスタマイズについて
詳しくは別記