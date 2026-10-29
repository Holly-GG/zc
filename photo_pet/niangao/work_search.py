"""Local application search. No screenshot, keyboard hook or API request."""
from .life.catalog import BY_ID
from .interaction.actions import ACTIONS
PAGES=[('陪伴总览',0,'年龄 心情 状态'),('照料与动作',1,'喝水 喂食 梳毛 猫砂 动作 图鉴'),('年糕小铺',2,'商城 购买 商品'),('我的背包',3,'物品 库存 摆放'),('专注与待办',4,'任务 番茄钟 计时'),('和年糕聊天',5,'API 对话 聊天'),('年糕日记',6,'公历 农历 日历'),('性格与设置',7,'接口 密钥 DeepSeek 性格 习惯 生日 设置')]
def search(query,tasks=()):
    words=str(query).strip().casefold().split()
    if not words:return []
    results=[]
    def matches(value):return all(word in value.casefold() for word in words)
    for title,page,tags in PAGES:
        if matches(title+' '+tags):results.append(dict(title='功能 · '+title,page=page,kind='page',id=''))
    for id,item in BY_ID.items():
        if matches(item['name']+' '+item['category']+' '+id):results.append(dict(title='物品 · '+item['name'],page=3,kind='item',id=id))
    for id,action in ACTIONS.items():
        if matches(action.label+' '+action.group+' '+id):results.append(dict(title='动作 · '+action.label,page=1,kind='action',id=id))
    for task in tasks:
        if isinstance(task,dict) and isinstance(task.get('text'),str) and matches(task['text']):results.append(dict(title=('已完成 · ' if task.get('done') else '待办 · ')+task['text'][:120],page=4,kind='task',id=task.get('id','')))
    return results[:60]
