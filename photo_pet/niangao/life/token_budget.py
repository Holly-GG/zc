"""Offline estimates are labelled; provider usage is the authoritative returned count."""
import json,math
from urllib.parse import urlsplit

def estimate(messages):
    approx=3;upper=512
    for message in messages:
        text=str(message.get('content',''));cjk=sum('\u2e80'<=c<='\u9fff' for c in text)
        approx+=8+math.ceil(cjk*1.5+(len(text.encode('utf-8'))-cjk*3)/3)
        upper+=len(text.encode('utf-8'))+32
    return {'estimated':max(1,approx),'conservative':upper,'method':'离线估算 / UTF-8 保守预算，非官方 tokenizer'}

def identity(settings):
    import hashlib
    value=json.dumps([settings.get('base_url','').rstrip('/'),settings.get('protocol','openai_chat'),settings.get('model','')],ensure_ascii=False)
    return hashlib.sha256(value.encode()).hexdigest()

def policy(settings):
    profiles=settings.get('context_profiles',{});p=profiles.get(identity(settings),{}) if isinstance(profiles,dict) else {}
    def number(key,default,low,high):
        v=p.get(key,default)
        return int(v) if isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) and low<=v<=high else default
    deepseek=urlsplit(settings.get('base_url','')).hostname=='api.deepseek.com'
    window=number('window',128000 if deepseek else 32768,4096,2000000)
    threshold=number('threshold',110000 if deepseek else 28000,1024,2000000)
    return {'window':window,'threshold':min(threshold,window-2048),'keep':number('keep',6,2,20)}

def usage_from(data,protocol):
    usage=data.get('usageMetadata' if protocol=='gemini' else 'usage')
    if not isinstance(usage,dict):return None
    def n(key):
        value=usage.get(key,0)
        return int(value) if isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value) and value>=0 else 0
    if protocol=='gemini':inp=n('promptTokenCount');out=n('candidatesTokenCount')+n('thoughtsTokenCount');total=n('totalTokenCount')
    elif protocol=='anthropic':inp=n('input_tokens')+n('cache_creation_input_tokens')+n('cache_read_input_tokens');out=n('output_tokens');total=0
    elif protocol=='openai_responses':inp=n('input_tokens');out=n('output_tokens');total=n('total_tokens')
    else:inp=n('prompt_tokens');out=n('completion_tokens');total=n('total_tokens')
    total=max(total,inp+out)
    return {'input':inp,'output':out,'total':total} if total>0 else None
