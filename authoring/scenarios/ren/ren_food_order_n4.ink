// 음식 주문 / N4 / ren
=== ren_food_order_n4 ===
丁寧に注文を始めます。 いい感じに決めよう。 #line:ren_food_order_n4_a01 #ko:정중하게 주문을 시작해요.
+ [注文してもいいですか] #line:ren_food_order_n4_u01a #ko:주문해도 될까요
  -> ren_food_order_n4_node_02
+ [このセットを一つお願いします] #line:ren_food_order_n4_u01b #ko:이 세트를 하나 부탁합니다
  -> ren_food_order_n4_node_02

条件をつけます。 いい感じに決めよう。 #line:ren_food_order_n4_a02 #ko:조건을 붙여요.
+ [辛さを少なめにできますか] #line:ren_food_order_n4_u02a #ko:매운맛을 약하게 할 수 있나요
  -> ren_food_order_n4_node_03
+ [ご飯を少なめにしてください] #line:ren_food_order_n4_u02b #ko:밥을 적게 해 주세요
  -> ren_food_order_n4_node_03

アレルギーを伝えます。 いい感じに決めよう。 #line:ren_food_order_n4_a03 #ko:알레르기를 전해요.
+ [卵が入っていますか] #line:ren_food_order_n4_u03a #ko:달걀이 들어 있나요
  -> ren_food_order_n4_node_04
+ [えびは食べられません] #line:ren_food_order_n4_u03b #ko:새우는 먹을 수 없습니다
  -> ren_food_order_n4_node_04

待ち時間を聞きます。 いい感じに決めよう。 #line:ren_food_order_n4_a04 #ko:대기 시간을 물어요.
+ [どのくらい時間がかかりますか] #line:ren_food_order_n4_u04a #ko:시간이 얼마나 걸리나요
  -> ren_food_order_n4_node_05
+ [すぐできますか] #line:ren_food_order_n4_u04b #ko:금방 되나요
  -> ren_food_order_n4_node_05

味の感想を言います。 いい感じに決めよう。 #line:ren_food_order_n4_a05 #ko:맛 감상을 말해요.
+ [とてもおいしいです] #line:ren_food_order_n4_u05a #ko:정말 맛있습니다
  -> ren_food_order_n4_node_06
+ [思ったより辛いです] #line:ren_food_order_n4_u05b #ko:생각보다 맵습니다
  -> ren_food_order_n4_node_06

持ち帰りを頼みます。 いい感じに決めよう。 #line:ren_food_order_n4_a06 #ko:포장을 부탁해요.
+ [持ち帰りにできますか] #line:ren_food_order_n4_u06a #ko:포장할 수 있나요
  -> END
+ [残りを包んでもらえますか] #line:ren_food_order_n4_u06b #ko:남은 것을 싸 주실 수 있나요
  -> END

-> END
