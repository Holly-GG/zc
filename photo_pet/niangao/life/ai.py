"""Opt-in OpenAI-compatible API. Key is encrypted with Windows user DPAPI."""
import json,urllib.request,urllib.parse,urllib.error,sys
from pathlib import Path
from email.utils import parsedate_to_datetime
class SecretVault:
    def __init__(self,path):self.path=Path(path);self.memory=""
    def save(self,key):
        key=key.strip()
        if not key:self.clear();return
        if sys.platform!="win32":self.memory=key;return
        import ctypes
        from ctypes import wintypes as w
        class BLOB(ctypes.Structure):_fields_=[("size",w.DWORD),("data",ctypes.POINTER(ctypes.c_ubyte))]
        raw=key.encode();buffer=ctypes.create_string_buffer(raw);source=BLOB(len(raw),ctypes.cast(buffer,ctypes.POINTER(ctypes.c_ubyte)));out=BLOB()
        crypt=ctypes.WinDLL("crypt32");crypt.CryptProtectData.argtypes=[ctypes.POINTER(BLOB),w.LPCWSTR,w.LPVOID,w.LPVOID,w.LPVOID,w.DWORD,ctypes.POINTER(BLOB)]
        if not crypt.CryptProtectData(ctypes.byref(source),"Niangao API",None,None,None,1,ctypes.byref(out)):raise OSError("Windows DPAPI 无法保存密钥")
        kernel=ctypes.WinDLL("kernel32");kernel.LocalFree.argtypes=[w.HLOCAL]
        try:self.path.parent.mkdir(parents=True,exist_ok=True);self.path.write_bytes(ctypes.string_at(out.data,out.size))
        finally:kernel.LocalFree(ctypes.cast(out.data,ctypes.c_void_p))
    def load(self):
        if sys.platform!="win32":return self.memory
        if not self.path.exists():return ""
        import ctypes
        from ctypes import wintypes as w
        class BLOB(ctypes.Structure):_fields_=[("size",w.DWORD),("data",ctypes.POINTER(ctypes.c_ubyte))]
        raw=self.path.read_bytes();buf=ctypes.create_string_buffer(raw);source=BLOB(len(raw),ctypes.cast(buf,ctypes.POINTER(ctypes.c_ubyte)));out=BLOB()
        crypt=ctypes.WinDLL("crypt32");crypt.CryptUnprotectData.argtypes=[ctypes.POINTER(BLOB),w.LPVOID,w.LPVOID,w.LPVOID,w.LPVOID,w.DWORD,ctypes.POINTER(BLOB)]
        if not crypt.CryptUnprotectData(ctypes.byref(source),None,None,None,None,1,ctypes.byref(out)):raise OSError("密钥不属于当前 Windows 用户或已损坏")
        kernel=ctypes.WinDLL("kernel32");kernel.LocalFree.argtypes=[w.HLOCAL]
        try:return ctypes.string_at(out.data,out.size).decode()
        finally:kernel.LocalFree(ctypes.cast(out.data,ctypes.c_void_p))
    def clear(self):self.memory="";self.path.unlink(missing_ok=True)
def checked_base(url):
    parsed=urllib.parse.urlsplit(url.strip())
    if parsed.username or parsed.password or parsed.query or parsed.fragment:raise ValueError("API 地址不能包含密码、查询参数或片段")
    if parsed.scheme!="https" and not (parsed.scheme=="http" and parsed.hostname in {"127.0.0.1","localhost","::1"}):raise ValueError("远程 API 必须使用 HTTPS；HTTP 仅限本机服务")
    if not parsed.hostname:raise ValueError("API 地址无效")
    return url.rstrip("/")
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        raise ValueError("API 重定向已阻止，请直接填写最终 HTTPS 接口地址")
class AIClient:
    def __init__(self,settings,vault):self.settings=settings;self.vault=vault;self.server_date=None
    def request(self,messages):
        if not self.settings.get("enabled"):raise ValueError("联网 AI 未开启")
        base=checked_base(self.settings["base_url"]);key=self.vault.load()
        if not key:raise ValueError("请先在设置中安全保存 API Key")
        payload=json.dumps({"model":self.settings["model"],"messages":messages,"max_tokens":700},ensure_ascii=False).encode()
        req=urllib.request.Request(base+"/chat/completions",data=payload,headers={"Content-Type":"application/json","Authorization":"Bearer "+key},method="POST")
        try:
            with urllib.request.build_opener(NoRedirect()).open(req,timeout=25) as response:
                raw=response.read(2_000_001)
                if len(raw)>2_000_000:raise ValueError("API 响应过大")
                header=response.headers.get("Date")
                if header:
                    try:self.server_date=parsedate_to_datetime(header).astimezone().date()
                    except (ValueError,TypeError):pass
                data=json.loads(raw)
            content=data["choices"][0]["message"]["content"]
            if not isinstance(content,str):raise ValueError("API 没有返回文字")
            return content[:10000]
        except urllib.error.HTTPError as exc:raise ValueError(f"API HTTP {exc.code}，请检查地址、模型与密钥权限") from None
        except urllib.error.URLError:raise ValueError("网络连接失败，已保留本地事件，请稍后重试") from None
    def chat(self,message,mood,history=None):
        system=f"你是布偶猫年糕，鼻侧有独特棕色小点。用简短温暖中文陪伴主人。当前游戏心情：{mood}。不要声称看见屏幕、读取键盘、实施现实操作或提供兽医诊断。"
        return self.request([{"role":"system","content":system}]+(history or [])[-8:]+[{"role":"user","content":message[:2000]}])
    def diary(self,events,mood):
        summary=[{"kind":e["kind"],"text":e["text"]} for e in events[-60:]]
        return self.request([{"role":"system","content":"用猫咪年糕第一人称写中文日记，150至300字。只依据提供的游戏事件，不虚构未发生的行为。"},
             {"role":"user","content":json.dumps({"events":summary,"mood":mood},ensure_ascii=False)}])
