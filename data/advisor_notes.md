# 顧問筆記（每次對話開頭先讀，結尾更新）

雲端（手機）版的 Claude 每次開新對話都不記得之前的事，靠這份筆記接續。
只寫策略與決定；不要寫個人資料或金鑰（repo 是公開的）。

## 本週（第 2 週，10/26–11/1）

### 誰是懂球帝 vs 永吉路懂球帝
- 10/30 17:14 截圖：6 勝 4 敗 1 平（FGM 139 平）。週四對手爆發：籃板 133-149、助攻 101-106 反超。
- 已做：Buzelis → Diabaté（10/28）、Sarr → Jaylen Wells（10/29）、Edey → Grayson Allen、Wells → Ayo Dosunmu（10/30 17:30 前）。Adds 6/8。
- 11/2 強力衝擊二連冠提案：Garland + Kel'el Ware 換 D. White + Diabaté。模擬（1500 次）贏尚恩 77% → 79%、例行賽 59% → 53%，在誤差內＝打平。建議拒絕（沒好處、White 的 FT%／抄截／阻攻符合打尚恩的方向，Garland TO 多）。
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

- ⚠️ 11/1 17:35：Draymond Green 美東週日休兵（背，O），Curry 也休（對手少一個射手）。改成 Allen → Neemias Queta（BOS，11/2 04:30 @ORL；M. Robinson 掛 Q 休兵，Queta 可能多打）。週一 LeBron 回來前釋出 Queta。
- ✅ 11/1 17:00 最終：LeBron（背，DTD，美東週六 B2B 缺陣，預計 11/2 回）移進 IL → 空出一個名單位。
  ① 簽 Podziemski，不用釋出；② Allen → Draymond（週日 1 場租用）；③ 週一 LeBron 回來前釋出 Draymond（釋出不算 add），把 LeBron 移回。
  長期模擬（rival，700 次，含每週串流 6 場）：放 Allen 89%／放 Diabaté 92%／放 Camara 88%／放 Draymond 93%——Allen 和 Diabaté 長期其實差不多（在誤差內），
  我先前說「Diabaté 長期價值高很多」講得太滿，已向使用者更正。
- 11/1 16:40 改計劃：週日放 Grayson Allen（不是 Diabaté）→ Podziemski，Camara → Draymond。Allen 本週已打完、本季 FG% .400 REB 3.0；Diabaté 本季 9.3 分 9.8 籃板 1.8 抄截 FG% .622，是籃板來源，保留（keep）。本週勝率三種放法都 96%。
- 10/31 19:50 新 FA 截圖：計劃不變（Podziemski、Draymond 都還是純 FA；週日 94%）。Draymond 被搶走就改 Queta（BOS，同 94%）。已用 save_plan 記進作戰卡，keep=Harper。

- ✅ 11/1 17:40 已做：+Podziemski（空位）、Allen → Queta。Adds 8/8 用完。週日先發 White、Podziemski、Reaves、WCJ、Queta 都在先發。
- 週一（台北 11/3 08:30 七六人開打前）：釋出 Queta、LeBron 移出 IL。長期模擬（500 次）：放 Queta 81%、放 Diabaté 80%（打平）、放 Camara 73%、放 Podziemski 73%、放 Dosunmu 76%、放 WCJ 74%。

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
- ⚠️ 11/1 17:35：Draymond 週日休兵，改用空位簽 Ja'Kobe Walter（TOR，可有可無，本週已近 100%）；週一 Embiid 回來前釋出。
- ✅ 11/1 17:00：Embiid（腳，DTD，預計 11/2 回）移進 IL → 空出名單位，直接簽 Draymond 不用釋出 Bey；週一 Embiid 回來前再釋出一人（大概是 Draymond）。
- 10/31 19:50 新 FA 截圖：Bey → Draymond Green 不變（save_plan 已記）；備案 De'Anthony Melton。
- ✅ 11/1 17:40 已做：+Ja'Kobe Walter（空位）。Adds 4/4 用完。
- 週一（台北 11/3 08:30 前）：釋出 Walter、Embiid 移出 IL。長期模擬（400 次）放 Walter 勝率最高（.593），其次放 Jackson／Dosunmu（.587），放 Bey .578、Kyshawn .582。
- 搖擺：FG%、ST、BLK；REB 大概輸；TO 放棄。
- 對手陣容（10/29）：Morant、Avdija、Kyrie、Brandon Miller、Buzelis、Anthony Black、Clingan、Gobert、Lillard、Fox、Giddey、Rollins、Jalen Green；IL Edey、Banchero、Nurkić。

## 第 3 週（11/2–11/8）作戰計劃（11/2 16:30 定案，FA 截圖 11/2 16:05）
- ⚠️ 11/2 16:05 截圖：Queta、Walter 還在、LeBron／Embiid 還在 IL（LeBron 健康、Embiid Q）→ 名單不合法，要先處理才能 Add。
- ✅ 11/2 16:19：IL 已處理（Queta、Walter 已放；LeBron、Embiid 回陣容），週一先發正確（懂球帝 Harper、White、Podziemski、Diabaté 坐板凳；baek's Bey、Jackson、DeRozan 坐板凳）。
- 11/2 交易後本週模擬（假設 11/4 生效）：原計劃（Brooks→Holiday→Turner）仍 92%，REB 68%→44%、3PTM 55%→70%、FG% 60%→51%；改長人接力 Brooks→Edey→Sharpe 91%（REB 58%）。維持原計劃，REB 變搖擺不硬拚。
- ✅ 11/2 16:31 已接受 Sun 交易並選定放 Diabaté；Yahoo 顯示 11/4 處理（聯盟投票中，3 票否決）。成交時放 Diabaté（Dosunmu 留著當串流位，週四照計劃換 Brooks）。
- 11/2 Sun 提案：Norman Powell + Ryan Rollins 換 WCJ（誰是懂球帝）。模擬（1500 次、含串流）贏尚恩 79% → 86%（Rollins 直接放）／91%（留 Rollins、放 Diabaté）。建議接受。
  2 換 1 要多放一人：Diabaté 或 Dosunmu 二選一；建議放 Diabaté、Dosunmu 繼續當串流位（留 Diabaté 就得放棄週四起的串流接力）。
- Fox vs Harper：本季 Fox 16.5/4.8/7.0、1.5 抄、FG% .576；Harper 18.5/5.5/4.8、FG% .473、FT% .895、TO 少；長期模型 Fox 排 65、Harper 158。本週搖擺 FG% → Fox 先發。
### 誰是懂球帝 vs Justin（不換 84%，照計劃 92%）
- 現在：Drop Queta、LeBron 移出 IL。週一先發坐板凳：White、Harper、Diabaté、Podziemski（最晚 11/3 08:00）。週三坐板凳：Harper、Diabaté。
- 串流位 Dosunmu 接力（3 adds）：① 11/5（四）中午後～11/6 10:00 前 Dosunmu → Dillon Brooks（PHX 四六）
  ② 11/6 13:00 後～11/7 11:00 前 Brooks → Jrue Holiday（POR 五六）③ 11/8 14:00 後～11/9 09:00 前 Holiday → Myles Turner（MIL 日，阻攻）。
- 比較過：Brooks→Sarr→Gafford 89%、Brooks→Edey→Sharpe 88%（籃板 80% 但三分 40%）；再加 Diabaté 第 2 位 92%（不划算、使用者想留）。
- 搖擺：3PTM 55%、3PT% 39%、FG% 60%；TO 必輸。剩 5 adds 不用（沒有可放的人）。
### baek's vs 安國（不換 31%，照計劃 41%）
- 現在：Drop Walter、Embiid 移出 IL（Q，週一可能打）。週一先發坐板凳：DeRozan、Isaiah Jackson、Bey（Turner 上，搶阻攻）。
- 串流位 Jackson 接力（2 adds）：① 11/5 14:00 後～11/6 10:00 前 Jackson → Collin Gillespie（PHX 四六，抄截 1.9、三分）② 11/8 13:00 後～11/9 10:00 前 Gillespie → Jeremiah Fears（NOP 日）。
- 比較過：再放 DeRozan 換 Melton 可到 ~49%，但整季模擬放 DeRozan 平均名次 3.4 → 5.1，不划算；Dosunmu 接力沒幫助。
- 守住 3PTM 81%、ST 74%、TO 60%、FT% 62%，再從 FG% 45%、BLK 38%、PTS 28% 拿一項就 5-4。REB、AST 放棄。

- 11/3 14:02 截圖（美東週一打完）：懂球帝 3-8（落後 FGM、FG%、3PTM、3PT%、PTS），預測 6-4-1；含交易＋接力本週約 81%（不交易 77%）。搖擺 FG% 33%、3PTM 59%、REB 47%。
  baek's 7-2（FG% .519、3PTM 34-15 大勝），不換 78%，照計劃 83–85%。最後一棒 Fears → 改 Tre Jones（FG% .515，保 FG% 領先；85% vs 83%）。

- 11/4 18:45：Sun 交易還沒處理（WCJ、Diabaté 還在）。強力衝擊二連冠又提案 Kel'el Ware 換 Diabaté → 建議拒絕：Diabaté 已綁在 Sun 交易裡（接受可能讓 Sun 交易失效）；
  改用 Dosunmu 換 Ware 模擬只有 70%（失去串流位），連放 Podziemski 留串流也是 91%，都不比現在 92% 好。
- 週三（台北 11/5 早上）先發：懂球帝改成 Diabaté、White 坐板凳（Harper、Fox 都上）——使用者質疑 Harper，模擬 15 種組合：坐 Diabaté+White 78.8% 最好、坐 Harper+Diabaté 76.8%。
  教訓：Harper 本季 18.3 分、FT% .875、TO 1.7，長期模型低估他（上季先驗拖累）；排先發要用本週模擬比較，不只看長期價值；baek's DeRozan、Bey、Jackson 坐板凳，Pritchard Q（08:30 開打）變 O 就換 Isaiah Jackson。

- 11/5 15:20 截圖（美東週三打完）：懂球帝 6-4（反超；3PTM 29-47、ST 14-20 落後，TO 41-60 大勝），預測 9-2，照計劃 95%。
  美東週三：Wemby 52 分 24 籃板 8 阻攻（三分 1/8）；Bam 35/10；Brunson、Booker 各 33；Harper 21/5 但 0 助攻；Camara 11 分 FG% .333 最差。
  baek's 6-2（FG% .530-.426、3PTM 59-28），預測 7-1-1，照計劃 96%。Luka 40 分、Embiid 26/15、Turner 12/9/6。
- 計劃不變（模擬 Brooks→Holiday→Turner 95% ≈ 改 Gafford 94%）。Sun 交易 11/5 15:27 截圖顯示沒有處理（WCJ、Diabaté 還在），✅ 確認被聯盟投票否決（Vetoed）。
- 11/5 改計劃：串流位改用 Diabaté（本週 97% vs 用 Dosunmu 94%；長期打平），Dosunmu 保留。

- ✅ 11/5 18:57：懂球帝 Diabaté → Brooks（adds 1/8）；baek's Jackson → Gillespie、DeRozan 進 IL（背痙攣，預計 11/7 回）（adds 1/4）。
- baek's 空出名單位：簽 Day'Ron Sharpe（BKN 六日，補 REB/ST；97% vs 不簽 94%）。週五我方 10 人有賽已滿，週六只 5 人。
  週日：DeRozan 若已恢復（IL 資格消失）→ 放 Gillespie、DeRozan 移出 IL（不簽 Tre Jones）；若仍 O → Gillespie → Tre Jones。
- ✅ 11/5 19:10 使用者已照第一版簽 Sharpe（adds 2/4），Draymond 方案作廢（多 0.7%，不值得再放人）。教訓：已經叫使用者做的動作，改計劃前先確認他做了沒。
- （作廢）11/5 19:20 改：baek's 空位先簽 Draymond（GSW 週四、六），週六 Draymond → Sharpe，週日 Gillespie → Tre Jones（98.1% vs 97.4%，用完 4 adds）。
  懂球帝不多串：Camara→Gillespie→Sarr 本週 98.4% vs 97.4%，但要永久放 Camara（長期價值高），不划算。
- 交易被否決的影響（rival，1500 次）：贏尚恩現在約 82%，交易成功約 94%（差 12%）。

- 11/6 14:20 截圖（美東週四打完）：懂球帝 8-3（不換 99%）；baek's 5-4（被追近，AST 90-104、ST 26-28、REB 129-133 落後，不換 89%）。
  週四：WCJ 27 分 13 籃板 10-12（超爆）、Brooks 24 分 4 三分 2 抄、Booker 30/8 助/3 抄、Bam 18/10、Podziemski 9/6 普通；Gillespie 6 分 2-9 但 3 抄。

- 11/6 安國（本週對手、聯盟第 1）提案：Podziemski + Randle + Anunoby + Suggs（O，膝，約 11/10）換 Luka + Turner。
  整季模擬（2000 次，放 Gillespie、Sharpe）：勝率 .569 vs .571、平均名次都 3.2、贏伊古達拉都 99%＝打平 → 建議拒絕（沒好處、名單被塞滿、送 Luka 給最強隊兼本週對手）。

- ✅ 11/6 23:20：懂球帝 Brooks → Holiday（adds 2/8），週五先發 9 人有賽全上 ✓。baek's 先發 ✓（Pritchard、AD 都 Q，08:00 開打前看）。
- ⚠️ DeRozan 由 O 改 Q（還在 IL）→ IL 資格可能失效、鎖住 Add/Drop。改計劃：現在就放 Gillespie、DeRozan 移出 IL（DEN 週六有賽，DeRozan > Gillespie）。週日 Tre Jones 那筆取消，剩 2 adds 週日再看。

- 11/7 20:25：懂球帝 8-2（1 平），baek's 5-4。baek's 已放 Gillespie、DeRozan 回陣容；AD 掛 O（腳踝）移進 IL → 空 1 個名單位。
  週五表現：懂球帝 Wemby 30/14、White 18 分 4 三分 5 助、Camara 18 分 4 三分、Harper 19、Holiday 12/7 助；LeBron 3-12、Reaves 8-22 偏差。
  baek's Luka 53 分、Kyshawn 33、NAW 28（10-10 罰球）、LaMelo 22/8 助、Dosunmu 26；Embiid 0-9、Turner 0-7 很差。對手 McDaniels 23、Acuff 22/8 助、Harden 17、Tatum 34/9 助（兩聯盟對手都有）。
- 週六計劃：懂球帝 Booker 在板凳要移上先發（換 Reaves 或 LeBron，他們週六沒賽）。baek's 空位簽 Cameron Johnson（DEN 週六，89.4% vs 不簽 85%）——11/7 21:00 作廢：AD 改 Q，移回陣容（WAS 週六有賽）；若已簽 Johnson 就放 Johnson。
  ⚠️ 位置限制：週六 9 人有賽但 6 個是後衛（Brunson、Booker、Fox、Harper、Podziemski、Holiday），後衛能放的只有 PG/SG/G/UTIL/UTIL 5 格，SF/PF/F 只有 Camara → Podziemski 坐板凳。
  教訓：排先發要看位置，不只看人數（Yahoo 位置：PG,SG,G,SF,PF,F,C,C,UTIL,UTIL）。串流挑人時優先補 SF/PF。
  週日：懂球帝 Holiday → Myles Turner；baek's 剩 1 add，週日看 FA 再決定。

- ✅ 11/8 全面檢查，找到並修正 3 個錯誤：①季末模擬從 10/26 開始，把已算進戰績的第 2 週又模擬一次、對手週次也錯位 → 改成從 sim_from（11/2）開始，第 3 週用目前比分（fixed_results）；
  ②11/8 早上的基準把 Holiday 和 Dosunmu 都拿掉（少算一人），62% 是錯的；③league_rosters 我方陣容沒同步（還有 Brooks、Gillespie）。
  修正後 10000 次：不交易 贏尚恩 94%、冠軍 64%；WCJ+Harper→Siakam+Rollins 98%、冠軍 76%、平均名次 2.1→1.3。
  敏感度（3000 次）：每週串流 3 場 73%→89%、不串流 32%→57%、先驗 8 場 99%→99%、40 場 90%→97%——交易在每種假設下都更好。
- （已作廢）11/8 更正：11/5「交易被否決後贏尚恩 82%」又多算了一個名單位（14 人＋串流），正確約 62%（2000 次）。
- 11/8 Sun 交易選項（rival 2000 次，基準 62%）：斑馬→Murray+Şengün+Siakam 82%（要放 Podziemski、WCJ）、斑馬→Murray+Durant 75%、斑馬→Murray+Şengün 69%；
  不動斑馬：Harper→Siakam 79%、Fox→Şengün 78%、Camara→Siakam 73%。Durant+Şengün／Embiid 組合都比不換差。
- 11/8 Sun 二對二方案（1200 次，基準 61%）：WCJ+Harper→Şengün+Rollins 85%、WCJ+Harper→Siakam+Rollins 84%、WCJ+Camara→Şengün+Rollins 80%；White→Siakam 62%（沒用）。
  說服點：Sun 弱 REB/ST/BLK/FG%（所以想要斑馬）→ WCJ 補籃板命中率；Harper 是新秀有潛力；Rollins 是他的板凳。Şengün 排名 24，太貴可能談不成，Siakam 版較實際。
- 11/8 Sun（懂球帝第 1 名）私下問 Wembanyama 能不能交易 → 建議不賣（全隊價值第一、遠超第二名，且 Sun 是奪冠最大對手）。真的開出具體條件再評估。

- 11/8 15:20 補上 Justin 陣容（VanVleet、Trae、A. Black、Jabari、Jaquez、Mobley、Sharpe、Jerome、N. Marshall＋板凳 Giannis、Acuff、LaVine、Coward、Tatum；IL Hart、Holmgren、Nurkić）→ 8 隊全部最新。
  10000 次：不交易 91%／冠軍 29%；WCJ+Harper→Siakam+Rollins 97%／冠軍 47%／平均名次 3.6→2.2。
- 11/8 15:00 同步：6 隊最新陣容（Justin 沒截，用 11/1 版、拿掉 Mara）、正式戰績、本週 4 場比分。強力衝擊二連冠變強：簽了 Diabaté、換來 Mara、D. Murray、Amen Thompson，戰績 15-7。尚恩本週 0 adds。
  重算（10000 次）：不交易 贏尚恩 90%、冠軍 32%；WCJ+Harper→Siakam+Rollins 97%、冠軍 48%、平均名次 3.5→2.2。
  3000 次：Harper→Siakam 96%、Fox→Şengün 96%、WCJ+Harper→Şengün+Rollins 97%（冠軍 53%）。
- 本週：懂球帝 8-3（預測 8-2-1、~100%），週日 Holiday → Myles Turner 照做。baek's 5-4（74%），週日不加人（加人反而拉低 TO、FT%）；REB、AST、ST 大概輸，靠 FG%、3PTM、PTS、BLK＋TO 52% 拿 5-4。

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
- ✅ 11/1 18:10 使用者已撤回交易。11/3 早上看 JJ 有沒有上場（ATL @IND 台北 08:30），沒事就重新提出。
- ⚠️ 11/1 18:00：Jalen Johnson 週六扭傷腳踝沒回場（ESPN DTD，預估 11/2 回，未確認）。建議先 Cancel trade，等他回來打 1–2 場確認沒事再重新提出（同樣 1 換 1）。
- ✅ 10/30 18:48 已送出 Brunson → Jalen Johnson（永吉路），等對方回覆。1 換 1、不加碼；被拒就不追。Yahoo 排名 JJ 第 20、Brunson 第 73。
- 交易提案 Brunson → Jalen Johnson（永吉路）：可以現在送。Brunson 本週最後一場是美東週五，JJ 是週六，投票期 1 天，生效時這週兩人都打完了，不影響本週。下週 JJ 4 場、Brunson 3 場。
  10/30 再驗證（兩組亂數各 1500 次）：贏尚恩 77–79% → 83–84%；REB 40%→69%、ST、BLK、AST 上升，3PTM 66%→56%、PTS、TO 下降。上季 JJ 22.5/10.3/7.9、FG% .489，比項聯盟價值高於 Brunson。
- 每週紀律：誰是懂球帝每週用滿 8 adds（優先籃板、命中率高的長人）；對上尚恩那週主攻 FT%、3PTM、3PT%、TO（他的弱項）。

## 第 2 週最終（11/2）：誰是懂球帝 9-2（只輸 FT%、TO）、baek's 6-3（FG% .447–.449、AST 152–153 各以極小差距輸）
- 累計：誰是懂球帝 14-8；尚恩 9-13（他輸 Justin 4-7）。baek's 9-8-1；伊古達拉約 8-10。

## 第 2 週回顧（11/1）與教訓
- 結果（週日前）：懂球帝 9-2、baek's 6-3，出賽 51 vs 42、47 vs 40。
- 教訓：①簽人前當天再查傷病／休兵（老將 B2B：Curry、Draymond、LeBron、Embiid；Draymond 是使用者先看到 O 才發現）；
  ②移人進 IL 後立刻重排先發（F 空格）；③陣容變動後重比所有放人選項；④預測要算對手剩餘場次；⑤adds 早點用（週一、二）效益較高。
- 第 3 週（11/2–11/8）賽程：每天 15/0/14/2/9/7/7 場；11/3（二）全休、11/5（四）只有 2 場 → 週四是串流重點日。
  懂球帝每天有賽 14/0/12/4/9/8/5 人（空格 24）；baek's 13/0/13/0/10/5/8（空格 27）。

## ⚠️ 11/1 勝率更正（誰是懂球帝 vs 尚恩）
- 10/30 的「每週串流 → 78–80%、交易後 84%」多算了一個名單位（虛擬串流球員加在 14 人之外）。
  正確算法（1500 次）：14 人固定不串流 22%；13 人＋1 個串流位每週 +3 場 23%、+6 場 54%、+9 場 63%。
- 串流位用誰（其餘 13 人保留）：Diabaté 56%、Dosunmu 54%、WCJ 50%、Camara 45% → Diabaté、Dosunmu 打平，照使用者偏好用 Dosunmu 當串流位（stream_slots），keep：Harper、Diabaté、Podziemski、Camara、WCJ。
- 意義：只靠串流不夠，還需要提升陣容（交易補籃板／助攻、對戰週打弱項）。
- 第 3 週草案（等 11/2 FA 截圖確認）：一 放 Queta、移回 LeBron；四（台北 11/5 下午～11/6 08:00）Dosunmu → Davion Mitchell（MIA 四、日）；
  之後串流位接力：五 Mitchell → 週五＋六的人（Holiday／Sarr／Vassell），日 → 週日的人（Gafford／Queta／Rollins）。週四只有 4 人有賽、空 6 格。
- plan.py 的貪婪法一次只看一步，看不出「接力換人」，第 3 週規劃要人工補；待改：多步接力搜尋。

## 整季賽程（11/1 網頁版 League → Standings → Schedule，存在 league_rosters.json 的 my_schedule）
- 誰是懂球帝：第 7、14 週對尚恩（約 11/30–12/6、1/18–1/24，週次日期以 Yahoo 為準）。季末模擬改用真實賽程後，贏過尚恩約 62%（串流 6 場／週、第 2 週 9-2）。
- baek's：第 10 週對伊古達拉（約 12/21–12/27）。贏過他約 99%。
- 第 3 週對手：誰是懂球帝 Justin's Ingenious Team；baek's 安國's Terrific Team（全聯盟最強）。

## 串流原則（11/5 驗證）
- 誰是懂球帝只開 1 個串流位（目前 Brooks 那格）。第 2 個串流位（放 WCJ／Podziemski／Camara、每週 +9 場）長期贏尚恩反而 66–71%，不如 1 個位 86%。
- 「用滿 8 adds」不是目標，目標是讓串流位每天都有人打（一週約 3–5 次 adds）。

## 長期備忘
- 誰是懂球帝設定（11/1 截圖）：交易 League Votes、3 票否決、Trade Reject Time 1 天；交易截止 2027-03-18；季後賽 6 隊 Week 20–22（到 4/4）；
  季後賽同戰績看「兩隊直接交手」→ 第 7、14 週對尚恩特別重要。Waiver 1 天、continual rolling list。
- 尚恩換人紀錄（11/1 截圖）：整季只有 5 筆——10/6 兩次（Hachimura、Watson）、10/13 交易 Zubac→Knueppel、10/20 Gafford→Zion、10/26 waiver 撿 Pritchard。
  分析：他是「長期價值型」——Ingram（O）→ Hachimura → Watson（同天反覆，略亂）；Zubac 換 Knueppel（排名 129→33，賺）；Gafford → Zion（150→45，賺）；週一 waiver 撿 Pritchard（56，好）。
  幾乎不串流，但陣容自然出賽多（第 2 週 47 場，比 Justin 45 還多），輸在比項結構：長人多、罰球三分弱，Zion 更加重這個弱點。
  注意：Knueppel 約 11/2 回來（場均 3.4 三分）會補他的三分弱點；他也可能繼續低價撿受傷的好球員。
  第 2 週只用 1 次 add，幾乎不串流。每週一看一次他的 Transactions（網頁版 League → Transactions，右上選他的隊）。
- Yahoo IL 規則（誰是懂球帝 11/1 公告，Yahoo 全站規則，兩聯盟都適用）：掛 O 的人放 IL，O 標記會保留到當晚交易處理時；
  只缺 1–2 場的人狀態恢復後就不再符合 IL 資格 → 要馬上移出 IL（先釋出一人），否則名單不合法，Yahoo 會鎖住所有 Add/Drop。
  缺 3 場以上或整季報銷的人，到回來前都可以一直放 IL。短期 O（B2B 休兵）也能拿來臨時空出名單位，但隔天就要處理。
- Jalen Williams（腓骨骨折開刀）、Cason Wallace（肩膀盂唇撕裂開刀）ESPN 預估都要到 2027-03 才回。
- Kon Knueppel（baek's IL，腿後肌）預計 11/2 前後回來（10/30 ESPN 改說「沒有時間表」），回來要記得移出 IL（要先釋出一人）。
- Yahoo 「Games Played 已打/總數」的總數只算目前排在先發的人，會低估剩餘場次；以賽程計算為準。
