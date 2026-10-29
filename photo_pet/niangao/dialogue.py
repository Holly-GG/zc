import random
import json
from collections import defaultdict,deque
from .art import asset_path
_CORPUS=json.loads(asset_path('data/dialogue.json').read_text(encoding='utf-8'))
_POOLS=defaultdict(list)
_RECENT=defaultdict(lambda:deque(maxlen=8))
for _row in _CORPUS:_POOLS[_row['context']].append(_row['text'])
def choose(kind,rng=None):
    kind=kind if kind in _POOLS else 'idle'
    choices=[text for text in _POOLS[kind] if text not in _RECENT[kind]]
    text=(rng or random).choice(choices or _POOLS[kind]);_RECENT[kind].append(text);return text
KEYWORDS=[(('喝水','补水'),'water'),(('吃饭','午饭','晚饭','早餐'),'feed'),(('累','休息'),'tired'),(('难过','伤心','焦虑'),'comfort'),(('睡','晚安'),'night'),(('开心','成功'),'happy'),(('学习','工作','专注','写作','代码'),'focus')]
def context_for(text):return next((context for words,context in KEYWORDS if any(word in text for word in words)),'todo')
def respond(text):return choose(context_for(text))
