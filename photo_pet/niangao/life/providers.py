"""Provider presets are editable suggestions; availability depends on the account/region."""
from urllib.parse import quote,urlsplit
PROTOCOLS={'openai_chat':'OpenAI 兼容 · Chat Completions','openai_responses':'OpenAI Responses','anthropic':'Claude / Anthropic Messages','gemini':'Gemini 原生 GenerateContent'}
PRESETS=[
 ('自定义 / OpenAI 兼容','openai_chat','',''),
 ('DeepSeek','openai_chat','https://api.deepseek.com/v1','deepseek-chat'),
 ('OpenAI','openai_chat','https://api.openai.com/v1','gpt-4.1-mini'),
 ('OpenAI · Responses','openai_responses','https://api.openai.com/v1',''),
 ('Claude / Anthropic','anthropic','https://api.anthropic.com/v1',''),
 ('Google Gemini','gemini','https://generativelanguage.googleapis.com/v1beta',''),
 ('通义千问 / 阿里百炼','openai_chat','https://dashscope.aliyuncs.com/compatible-mode/v1','qwen-plus'),
 ('Kimi / Moonshot','openai_chat','https://api.moonshot.cn/v1',''),
 ('智谱 GLM','openai_chat','https://open.bigmodel.cn/api/paas/v4',''),
 ('硅基流动','openai_chat','https://api.siliconflow.cn/v1',''),
 ('豆包 / 火山方舟','openai_chat','https://ark.cn-beijing.volces.com/api/v3',''),
 ('文心 / 百度千帆（兼容）','openai_chat','https://qianfan.baidubce.com/v2',''),
 ('OpenRouter','openai_chat','https://openrouter.ai/api/v1',''),
 ('Groq','openai_chat','https://api.groq.com/openai/v1',''),
 ('Mistral','openai_chat','https://api.mistral.ai/v1',''),
 ('Ollama 本机','openai_chat','http://localhost:11434/v1',''),
 ('LM Studio 本机','openai_chat','http://localhost:1234/v1','')]

def reasoning_model(model):
    name=model.lower().split('/')[-1]
    return any(token in name for token in ('reasoner','reasoning','thinking','deepseek-r1','qwen3')) or name.startswith(('o1','o3','o4','gpt-5','gemini-2.5','gemini-3'))

def endpoint(base,protocol,model):
    path=urlsplit(base).path.rstrip('/')
    suffix={'openai_chat':'/chat/completions','openai_responses':'/responses','anthropic':'/messages'}.get(protocol)
    if suffix:
        if path.endswith(suffix):return base
        if path.endswith(('/chat/completions','/responses','/messages',':generateContent')):raise ValueError('接口路径与协议不匹配，请检查协议选项')
        return base+suffix
    if protocol=='gemini':
        if path.endswith(':generateContent'):return base
        if path.endswith(('/chat/completions','/responses','/messages')):raise ValueError('Gemini 原生接口与当前地址不匹配')
        model=model.removeprefix('models/')
        return base+'/models/'+quote(model,safe='')+':generateContent'
    raise ValueError('未知 API 协议，请重新选择')

def bounded_int(value,default,low,high):
    return max(low,min(high,int(value))) if isinstance(value,(int,float)) and not isinstance(value,bool) and low<=value<=high else default

def build_request(settings,messages,key,test=False):
    protocol=settings.get('protocol','openai_chat');model=str(settings.get('model','')).strip()
    if not model or len(model)>200 or any(ord(ch)<32 for ch in model):raise ValueError('请填写控制台实际可用的模型 ID，不能包含换行')
    if any(ch in key for ch in ('\r','\n')):raise ValueError('API Key 不能包含换行')
    base=settings['base_url'];url=endpoint(base,protocol,model)
    reasoning=reasoning_model(model)
    limit=bounded_int(settings.get('max_tokens'),700,64,16384)
    if test:limit=64
    if reasoning:limit=max(limit,4096 if test else 8192)
    timeout=bounded_int(settings.get('timeout'),90,10,180)
    headers={'Content-Type':'application/json','Accept':'application/json'}
    if protocol=='openai_chat':
        headers['Authorization']='Bearer '+key
        payload={'model':model,'messages':messages,'stream':False}
        # OpenAI reasoning families reject legacy max_tokens. Other compatible services keep it.
        field='max_completion_tokens' if model.lower().startswith(('o1','o3','o4','gpt-5')) else 'max_tokens'
        payload[field]=limit
        if urlsplit(base).hostname=='dashscope.aliyuncs.com' and 'qwen3' in model.lower():payload['enable_thinking']=False
    elif protocol=='openai_responses':
        headers['Authorization']='Bearer '+key
        payload={'model':model,'input':messages,'max_output_tokens':max(limit,2048) if reasoning else limit,'stream':False,'store':False}
    elif protocol=='anthropic':
        headers.update({'x-api-key':key,'anthropic-version':'2023-06-01'})
        payload={'model':model,'system':'\n'.join(m['content'] for m in messages if m['role']=='system'),'messages':[m for m in messages if m['role']!='system'],'max_tokens':limit,'stream':False}
    elif protocol=='gemini':
        headers['x-goog-api-key']=key
        payload={'systemInstruction':{'parts':[{'text':'\n'.join(m['content'] for m in messages if m['role']=='system')}]},'contents':[{'role':'model' if m['role']=='assistant' else 'user','parts':[{'text':m['content']}]} for m in messages if m['role']!='system'],'generationConfig':{'maxOutputTokens':max(limit,4096) if reasoning else limit}}
    else:raise ValueError('未知 API 协议')
    return url,headers,payload,timeout

def list_value(value):return value if isinstance(value,list) else []

def text_parts(content):
    if isinstance(content,str):return content
    if not isinstance(content,list):return ''
    return '\n'.join(part['text'] for part in content if isinstance(part,dict) and isinstance(part.get('text'),str) and part.get('type','text') in ('text','output_text'))

def parse_reply(data,protocol):
    if not isinstance(data,dict) or data.get('error'):raise ValueError('服务返回错误；请检查模型、权限和余额')
    text=''
    if protocol=='openai_chat':
        choices=list_value(data.get('choices'))
        if choices and isinstance(choices[0],dict):
            message=choices[0].get('message',{})
            if isinstance(message,dict):
                if message.get('refusal'):raise ValueError('模型拒绝了本次请求，请换一条普通聊天内容测试')
                text=text_parts(message.get('content'))
                if not text and message.get('reasoning_content'):raise ValueError('模型仅返回思考过程，尚未给出正文；请增加输出预算或使用非思考模型')
    elif protocol=='anthropic':text=text_parts(data.get('content'))
    elif protocol=='gemini':
        candidates=list_value(data.get('candidates'))
        if candidates and isinstance(candidates[0],dict):
            content=candidates[0].get('content',{})
            if isinstance(content,dict):
                text='\n'.join(p['text'] for p in list_value(content.get('parts')) if isinstance(p,dict) and isinstance(p.get('text'),str) and not p.get('thought'))
    elif protocol=='openai_responses':
        text='\n'.join(text_parts(item.get('content')) for item in list_value(data.get('output')) if isinstance(item,dict) and item.get('type')=='message')
    if not text.strip():raise ValueError('接口已响应但没有可显示的正文；请检查协议、模型及输出预算')
    return text.strip()[:10000]
