from dataclasses import dataclass
@dataclass(frozen=True)
class Action:
    label:str
    group:str
    resource:str
    sound:str=""
    seconds:float=3.2
    note:str=""
ROWS={
 "a":["knead","rub_hand","roll","nibble"],
 "b":["hang","struggle","fear_ball","startle_jump"],
 "c":["scratch","slow_groom","lick_paw","tail_sway"],
 "d":["stalk","hunt_wiggle","pounce","miss"],
 "e":["rub_mouse","chew_toy","swat","dodge"],
 "f":["keyboard_paw","peek_screen","typing_nod","leg_rub"],
 "g":["angry_shake","ignore","puff","ear_flick"],
 "h":["shy","expectant","bored","excited"]}
LABELS=[
 ("knead","踩奶","抚摸","purr"),("rub_hand","蹭手撒娇","抚摸","purr"),("roll","随地打滚 / 翻肚皮","日常",""),
 ("nibble","轻啃指尖","抚摸","smack"),("hang","乖乖悬挂","抱起","milk_meow"),("struggle","悬空蹬腿 / 挣扎","抱起","adult_meow"),
 ("fear_ball","害怕缩成球","抱起","senior_meow"),("startle_jump","受惊跳起","戳击","adult_meow"),
 ("scratch","磨爪子","日常","scratch"),("slow_groom","慢舔身体","日常",""),("lick_paw","舔爪子","日常","smack"),
 ("tail_sway","悠闲甩尾","日常",""),("stalk","潜行 / 蹲守光标","光标",""),("hunt_wiggle","摇屁股蓄力","逗弄","bell"),
 ("pounce","蹦跳扑抓","逗弄",""),("miss","扑空失落","光标","senior_meow"),("rub_mouse","蹭鼠标","光标","purr"),
 ("chew_toy","啃玩具","逗弄","smack"),("swat","左右扑抓","逗弄","bell"),("dodge","左右躲闪","逗弄",""),
 ("keyboard_paw","扒键盘 / 拍按键","打字",""),("peek_screen","探头看屏幕","打字",""),("typing_nod","跟着敲击点头","打字",""),
 ("leg_rub","开心蹭腿（不含真人腿）","投喂","purr"),("angry_shake","生气甩头","戳击","hiss"),("ignore","扭头不理 / 哼唧","戳击","adult_meow"),
 ("puff","受惊炸毛","戳击","hiss"),("ear_flick","甩耳朵","日常",""),("shy","害羞","情绪","milk_meow"),
 ("expectant","期待 / 歪头","情绪","adult_meow"),("bored","无聊发呆","情绪",""),("excited","兴奋","情绪","bell")]
ACTIONS={key:Action(label,group,key,sound) for key,label,group,sound in LABELS}
for key,label,sound in [("idle","安静陪伴",""),("walk","到处探索",""),("sleep","蜷身睡觉","snore"),("pet","舒服眯眼","purr"),
 ("feed","低头干饭","smack"),("groom","舔毛",""),("stretch","伸懒腰",""),("play_bow","前伏邀请玩耍","bell"),("yawn","打哈欠","senior_meow")]:
    ACTIONS[key]=Action(label,"基础",key,sound,4)
for key,label,resource,sound,note in [
 ("elegant_walk","优雅踱步","walk","","与探索共用双向步态，降低实际移动速度"),
 ("sleepy","犯困","yawn","snore","复用哈欠姿态，随后可进入睡眠"),
 ("sad","委屈","miss","senior_meow","复用扑空失落的低头姿态"),
 ("purr_eyes","眯眼呼噜","pet","purr","复用摸头眯眼姿态"),
 ("mouth_lick","吃完舔嘴 / 吧唧嘴","feed","smack","使用进食图集的收尾帧"),
 ("cursor_trophy","叼住光标炫耀（模拟）","chew_toy","bell","共用啃玩具姿态，附模拟光标标记；不抓取系统光标")]:
    ACTIONS[key]=Action(label,"变体",resource,sound,3.2,note)
MOOD_POOLS={
 "害羞":["shy","rub_hand"],"委屈":["sad","expectant"],"生气":["angry_shake","ignore"],"焦躁":["ear_flick","angry_shake"],
 "犯困":["sleepy","yawn"],"兴奋":["excited","hunt_wiggle","swat"],"无聊":["bored","scratch","tail_sway"],
 "期待":["expectant","stalk"],"低落":["sad","shy"],"平静":["slow_groom","tail_sway","lick_paw"],
 "开心":["knead","rub_hand","roll","stretch"]}
SOUNDS={"milk_meow":"奶喵叫","adult_meow":"成猫喵呜","senior_meow":"老猫低唤","purr":"呼噜","smack":"吧唧",
        "hiss":"哈气","scratch":"抓挠","bell":"铃铛","snore":"打呼"}
