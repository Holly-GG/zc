"""One profile source for every API request. Unfilled facts stay explicitly unknown."""
from copy import deepcopy
from .age import age_info
DEFAULT_PROFILE={"name":"Niangao","display_name":"年糕","sex":"male","breed":"Ragdoll",
 "personality":"","habits":"","likes":"","dislikes":"","speaking_style":"","owner_name":"","notes":""}
LIMITS={"name":60,"display_name":60,"sex":30,"breed":60,"personality":800,"habits":800,"likes":300,"dislikes":300,"speaking_style":300,"owner_name":80,"notes":500}
def sanitize_profile(value):
    source=value if isinstance(value,dict) else {}
    return {key:(source[key][:LIMITS[key]].strip() if isinstance(source.get(key),str) else default) for key,default in DEFAULT_PROFILE.items()}
def snapshot(engine):
    profile=sanitize_profile(engine.data.get("profile"));real=age_info(engine.data["birth_date"],engine.today())
    return {"identity":profile,"birth_date":engine.data["birth_date"],"real_age":real["text"],"real_stage":real["stage"],
     "virtual_age_months":engine.data["age_override"],"mood":engine.mood,"stats":deepcopy(engine.data["stats"]),
     "appearance":"蓝眼睛、深棕面罩与耳朵、不对称白纹、粉鼻旁查看者右侧有棕点、白色胸腹与爪子、蓬松长毛",
     "profile_rule":"空白字段代表未知，不得编造真实习惯；虚拟体验年龄不能冒充真实年龄"}
