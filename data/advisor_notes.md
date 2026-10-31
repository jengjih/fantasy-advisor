# 顧問筆記（每次對話開頭先讀，結尾更新）

雲端（手機）版的 Claude 每次開新對話都不記得之前的事，靠這份筆記接續。
只寫策略與決定；不要寫個人資料或金鑰（repo 是公開的）。

## 本週（第 2 週，10/26–11/1）

### 誰是懂球帝 vs 永吉路懂球帝
- 10/30 17:14 截圖：6 勝 4 敗 1 平（FGM 139 平）。週四對手爆發：籃板 133-149、助攻 101-106 反超。
- 已做：Buzelis → Diabaté（10/28）、Sarr → Jaylen Wells（10/29）、Edey → Grayson Allen、Wells → Ayo Dosunmu（10/30 17:30 前）。Adds 6/8。
- 拒絕交易：桐生一馬用 Edgecombe + Kawhi + Randle 換 Brunson + Bam。
- 10/30 17:15 計劃（plan.py＋模擬：照做贏 97%，不換 78%）：
  ① 今天～台北 10/31 07:00 前：Edey → Grayson Allen（CHA，週五週六）、Wells → Ayo Dosunmu（MIN，週五週六）。Edey、Wells 週五都沒賽，現在就能換。
  ② 週日（週六打完後、台北 11/2 09:00 前）：Diabaté → Brandin Podziemski（GSW）、Camara → Draymond Green（GSW，補籃板）。
  plan.py 又建議放 Dylan Harper，不採用（潛力新秀；換 Camara 勝率一樣 97%）。
- 搖擺：3PTM（不換 44%）、REB（54%）、FGM；FT%、TO 必輸。
- 對手陣容（10/29）：Curry、RJ Barrett、Dejounte Murray、Saddiq Bey、Jalen Johnson、Achiuwa、Jokić、Jarrett Allen、Kyrie、
  Robert Williams III（膝，DTD）、Wiggins、Markkanen（腕，DTD）、Jalen Smith（手指，DTD）、Paul George；IL Banchero。

- 10/30 17:35 換完後模擬：不再換 93%（預測 9-2）；週日照計劃換 97%。週六要把板凳的 Wemby、Fox、Harper、Camara 移上先發（週六 8 人有賽）。

- 10/31 13:43 截圖（美東週五打完）：6 勝 5 敗。REB 193-190 反超；3PTM 53-55、3PT%、AST 138-149 被反超。plan.py 預測 9-2；不換 78%，週日照計劃 94%。
  週日計劃不變：Diabaté → Podziemski、Camara → Draymond Green（94%；plan.py 又建議放 Harper 換 Queta，一樣 94%，不採用）。

- 10/31 19:50 新 FA 截圖：計劃不變（Podziemski、Draymond 都還是純 FA；週日 94%）。Draymond 被搶走就改 Queta（BOS，同 94%）。已用 save_plan 記進作戰卡，keep=Harper。

### baek's Grand League vs LALA好
- 10/30 17:13 截圖：4 勝 5 敗。贏 FG%(.446-.444)、FT%、3PTM(44-42)、BLK(18-17)；輸 PTS(352-368)、REB(96-124)、AST(84-92)、ST(20-22)、TO。Adds 已用 2/4。
- 已做：Mitchell Robinson → Saddiq Bey（10/28）、Ayton → Scotty Pippen Jr.（10/29）、Pippen → Isaiah Jackson（10/30）。Adds 3/4。
- 拒絕交易：安卓·伊古達拉用 Jerami Grant 換 Dosunmu。
- Luka 10/30 已不在 ESPN 傷病名單（健康）。對手 Morant 腿後肌 DTD（預計 10/31）。
- 10/30 17:15 計劃（模擬：照做贏 96%，不換 89%；plan.py 預測 7-2）：
  ① 今天～台北 10/31 08:00 前：Pippen → Isaiah Jackson（LAC C，週五＋週日；補 FG%、BLK、ST）。plan.py 原本建議 Keaton Wagler，但他命中率 .316，Jackson 讓 FG% 贏面 48%→63%。
  ② 週日（週六打完後、台北 11/2 09:00 前）：Bey → Draymond Green（GSW）。
- 10/30 17:35 換完後模擬：不再換 91%（預測 7-2）；週日 Bey → Draymond Green 96%。週六要把板凳的 Turner、NAW、Bey 移上先發（週六 7 人有賽）。
- 10/31 13:43 截圖：5 勝 4 敗（FG% .446-.447 幾乎平手）。預測 7-2，本週贏約 100%。週日 Bey → Draymond Green 照做。
- 10/31 19:50 新 FA 截圖：Bey → Draymond Green 不變（save_plan 已記）；備案 De'Anthony Melton。
- 搖擺：FG%、ST、BLK；REB 大概輸；TO 放棄。
- 對手陣容（10/29）：Morant、Avdija、Kyrie、Brandon Miller、Buzelis、Anthony Black、Clingan、Gobert、Lillard、Fox、Giddey、Rollins、Jalen Green；IL Edey、Banchero、Nurkić。

## 宿敵監控（10/30 截圖）
- 誰是懂球帝「尚恩·李文斯頓」（第 1 週 5-6-0、8 隊第 6）：Luka、Cade Cunningham、Pritchard、Mikal Bridges、Avdija、Dyson Daniels、Sabonis、Gobert、Coby White（O）、Okongwu；
  板凳 Harden、Peyton Watson、Zion、Herro；IL Knueppel。第 2 週對 Justin（8-3 第 1）目前 8-3 領先，但模擬只有 48% 贏（對手剩餘場次多）。
  長處 BLK、FG%、ST、AST（長人多）；弱點 FT%、3PTM、3PT%。對上他時主攻罰球、三分。
- baek's Grand League「安卓·伊古達拉」（3-6-0、12 隊第 10）：SGA、Cade Cunningham、Vassell、Quentin Grimes、Jerami Grant、Tari Eason、Kalkbrenner、Hartenstein、Reed Sheppard（O）、Poeltl；
  板凳 Camara、Champagnie；IL Duren（O）。第 2 週對溜馬三劍客 4-5，模擬只有 15% 贏。
  除了 SGA、Cade 之外很薄，PTS/REB/AST 量不夠；長處 FG%、FT%、TO。曾想用 Grant 換 Dosunmu，可能還會找交易。

- 10/30 季末強弱初估（ESPN 全季賽程、上季 20 場先驗、每日先發上限、傷病回歸日；兩隊陣容固定、不算串流）：
  誰是懂球帝 我 vs 尚恩 每週贏約 40%（5.1-5.7；我強 FT%、TO、BLK，弱 REB 15%、AST 14%）；
  baek's 我 vs 伊古達拉 每週贏約 90%。要做全聯盟季末排名，需要使用者提供：每隊陣容、戰績表、賽程（每週對手）、季後賽／All-Star 週設定。

- 10/30 誰是懂球帝全聯盟季末預測（season.py，2000 次，上季先驗 8/20/40 場結果都差不多）：
  Sun 最強（勝率 .60、冠軍 ~40%）、尚恩第 2（.57、冠軍 ~20%）、永吉路 .50、我 .48–.49 排第 4–5、進季後賽 80–85%、冠軍 17–20%
  （季後賽時 Jalen Williams、Cason Wallace 回來，所以奪冠機率比排名高）。我的弱項：REB（對全聯盟只贏 24%）、FG%、FGM、3PT%；強項 BLK、FT%、AST、TO。
  Justin 目前 8-3 第 1，但模擬掉到 6–7 名（Giannis、Tatum 之外偏弱）。

- 10/30 baek's 季末預測（12 隊陣容齊全，2000 次）：安國 .625 第 1、冠軍 31%；我 .581 平均第 3、季後賽 100%、冠軍 17%；
  LALA好（目前 2-7）預測第 3（REB 92%、AST 89%、BLK 84%）、溜馬第 4（冠軍 25%）；無慼 8-1 預測掉到第 6；eric's 第 8（93%）；
  伊古達拉 .427 第 9–10，季後賽只有 8%。我的弱項 FG%（32%）、ST 45%、REB 51%；強項 3PTM 92%、PTS 85%、FT% 72%。補強方向：命中率高的長人。

## 🎯 終極目標（10/30 使用者定）：兩個聯盟最終名次都贏宿敵（各賭 1000）
- 假設「贏」＝季末最終名次（含季後賽）排在宿敵前面；待使用者確認賭約怎麼算。
- 模擬結果（season.py＋虛擬串流位，1500 次）：
  誰是懂球帝 vs 尚恩：不串流只有 30%；每週多串 2/4/6 場 → 44%/64%/78~80%。尚恩本週只用 1 次 add，串流是最大槓桿。
    每週空先發格約 21 格，用滿 8 adds 多打 6 場做得到。
    交易（在串流 +6 的基礎上）：Brunson→Jalen Johnson（永吉路）84%、Fox→Clingan（桐生）80%、White→Lendeborg 82%、Booker+Diabaté→Holmgren+Mobley 81%；
    Booker→Towns／Giannis 沒有明顯幫助。交易只多 2–6%，雜訊約 ±3%。
  baek's vs 伊古達拉：現況已經 99%（他季後賽只有 8%）。原則：不跟伊古達拉交易、不送他補強。
- ✅ 10/30 18:48 已送出 Brunson → Jalen Johnson（永吉路），等對方回覆。1 換 1、不加碼；被拒就不追。Yahoo 排名 JJ 第 20、Brunson 第 73。
- 交易提案 Brunson → Jalen Johnson（永吉路）：可以現在送。Brunson 本週最後一場是美東週五，JJ 是週六，投票期 1 天，生效時這週兩人都打完了，不影響本週。下週 JJ 4 場、Brunson 3 場。
  10/30 再驗證（兩組亂數各 1500 次）：贏尚恩 77–79% → 83–84%；REB 40%→69%、ST、BLK、AST 上升，3PTM 66%→56%、PTS、TO 下降。上季 JJ 22.5/10.3/7.9、FG% .489，比項聯盟價值高於 Brunson。
- 每週紀律：誰是懂球帝每週用滿 8 adds（優先籃板、命中率高的長人）；對上尚恩那週主攻 FT%、3PTM、3PT%、TO（他的弱項）。

## 長期備忘
- Jalen Williams（腓骨骨折開刀）、Cason Wallace（肩膀盂唇撕裂開刀）ESPN 預估都要到 2027-03 才回。
- Kon Knueppel（baek's IL，腿後肌）預計 11/2 前後回來（10/30 ESPN 改說「沒有時間表」），回來要記得移出 IL（要先釋出一人）。
- Yahoo 「Games Played 已打/總數」的總數只算目前排在先發的人，會低估剩餘場次；以賽程計算為準。
