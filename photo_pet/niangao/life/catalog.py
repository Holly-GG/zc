# Fictional in-game coins only; unavailable wearable assets are never sold.
def item(id,name,category,price,kind="consumable",effect=None,minimum=0,maximum=10000,ready=True,note=""):
    return dict(id=id,name=name,category=category,price=price,kind=kind,effect=effect or {},minimum=minimum,maximum=maximum,ready=ready,note=note)
CATALOG=[
 item("milk","羊奶粉","食品",8,effect={"satiety":18},maximum=3),
 item("kitten_food","幼猫粮","食品",12,effect={"satiety":26},minimum=3,maximum=12),
 item("food","全价猫粮","食品",12,effect={"satiety":28},minimum=3),
 item("fish","小鱼干","食品",10,effect={"satiety":8,"mood":12},minimum=3),
 item("freeze_dried","冻干","食品",16,effect={"satiety":14,"mood":15},minimum=3),
 item("wet_food","肉罐头","食品",18,effect={"satiety":30,"mood":10},minimum=3),
 item("cat_strip","猫条","食品",12,effect={"satiety":8,"mood":16},minimum=3),
 item("senior_food","老年易消化粮","食品",14,effect={"satiety":26,"health":3},minimum=84),
 item("happy_snack","快乐零食","食品",22,effect={"satiety":10,"mood":25},minimum=3),
 item("energy_snack","精力零食","食品",20,effect={"energy":18,"satiety":6},minimum=3),
 item("clean_snack","清洁零食（虚拟）","食品",18,effect={"cleanliness":16},minimum=3),
 item("wand","逗猫棒","玩具",35,"toy",{"mood":10}),item("ball","弹力小球","玩具",28,"toy",{"mood":8}),
 item("mouse","发条老鼠","玩具",40,"toy",{"mood":12}),item("feather","羽毛玩具","玩具",26,"toy",{"mood":8}),
 item("bell_ball","铃铛球","玩具",32,"toy",{"mood":9}),item("catnip","猫薄荷玩偶","玩具",45,"toy",{"mood":14}),
 item("bed","软垫猫窝","家具",40,"furniture"),item("bowl","食盆水盆","家具",25,"furniture"),
 item("scratcher","猫抓板","家具",35,"furniture"),item("rug","暖色地毯","家具",45,"furniture"),
 item("plant","安全绿植摆件","家具",30,"furniture"),item("lamp","陪伴小台灯","家具",55,"furniture"),
 item("tree","猫爬架","家具",100,"furniture",note="桌面平台互动；照片姿态与路径演出，非 3D 骨骼攀爬"),
 item("hammock","窗台吊床","家具",80,"furniture",note="桌面休息与瞭望"),item("litter","猫砂盆","家具",45,"furniture"),
 item("bow","蝴蝶结","装扮",45,"outfit",ready=False,note="服饰贴合与穿模检查未完成，不出售"),
 item("scarf","节日围巾","装扮",65,"outfit",ready=False,note="长毛与布料碰撞未完成，不出售"),
 item("crown","小皇冠","装扮",80,"outfit",ready=False,note="头部适配未完成，不出售"),
 item("freeze_age","年龄冻结剂","道具",75,"age_freeze"),item("kitten_candy","幼猫体验糖（行为）","道具",60,"age_kitten",note="只体验幼猫行为节奏，不伪造幼年真实照片"),
 item("comfort","安抚抱枕","道具",25,effect={"mood":22,"energy":6}),item("cleaner","一键清洁","道具",25,effect={"cleanliness":40}),
 item("affection","好感礼盒","道具",35,effect={"mood":30}),item("stars","星光边饰","特效",60,"effect",ready=False,note="特效贴合尚未校验，不出售"),item("petals","花瓣边饰","特效",60,"effect",ready=False,note="特效贴合尚未校验，不出售"),
 item("room_garden","花园草地","空间",150,"room"),item("room_balcony","阳台","空间",120,"room"),item("room_kitchen","厨房","空间",120,"room"),
 item("material_pack","自定义立绘包","素材",0,"import",note="通过设置导入 PNG，不运行陌生代码")]
RETIRED_ROOMS={x["id"]:x for x in CATALOG if x["kind"]=="room"}
CATALOG=[x for x in CATALOG if x["kind"]!="room"]
CATALOG.extend([
 item("food_bowl","年糕粮碗","照料",25,"furniture",note="可放到桌面，点击补充基础餐"),
 item("water_bowl","清水小碗","照料",20,"furniture",note="有水位与涟漪，右键可补水"),
 item("water_fountain","猫耳自动饮水机","照料",65,"furniture",note="循环水流与水位；没水时暂停，右键补水"),
 item("brush","软毛梳","照料",22,"furniture",note="摆到桌面，点击给年糕梳毛"),
 item("wash_basin","泡泡洗澡盆","照料",45,"furniture",note="点击进行虚拟清洁"),
 item("health_kit","安心照料包（虚拟）","照料",35,"furniture",note="游戏内健康照料，不替代兽医诊断"),
 item("water_bottle","随身补水瓶","食品",8,effect={"health":2},note="虚拟补水用品，可摆放与使用")])
CATALOG.extend([
 item("tunnel","躲猫猫隧道","玩具",55,"toy",{"mood":12}),
 item("laser","小爪激光笔","玩具",38,"toy",{"mood":9},note="模拟红点，不控制系统光标"),
 item("soft_bed","奶油软垫窝","家具",48,"furniture"),
 item("blanket","云朵小毯子","家具",30,"furniture"),
 item("garden_patch","蝴蝶草地垫","家具",65,"furniture",note="二维桌面摆件，非 3D 空间"),
 item("freeze_piece","一颗冻干","食品",2,effect={"satiety":2,"mood":2},minimum=3,note="冻干右键一次掉一颗")])
BY_ID={x["id"]:x for x in CATALOG}
def is_placeable(id):
    it=BY_ID.get(id)
    return bool(it and it["ready"] and it["kind"] not in ("import","room"))

SCENES={"desk":"书桌","living":"客厅","bedroom":"卧室","garden":"花园草地","balcony":"阳台","kitchen":"厨房"}

LARGE_ITEMS={"tree":230,"hammock":210,"tunnel":190,"bed":180,"soft_bed":180,"rug":190,"blanket":180,"garden_patch":220}
def desktop_width(id):return 38 if id=="freeze_piece" else LARGE_ITEMS.get(id,112)
