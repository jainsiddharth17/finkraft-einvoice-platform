import os, httpx
from dataclasses import dataclass
@dataclass
class SubmitResult:
    accepted: bool
    external_id: str|None=None
    initial_status: str|None=None
    unknown: bool=False
    error: dict|None=None
class ASPAAdapter:
    """ASP A synchronous POST /invoices and polling GET /invoices/{submission_id}."""
    def __init__(self):
        self.base=os.getenv("ASP_A_BASE_URL","http://localhost:9001").rstrip("/")
        self.key=os.getenv("ASP_A_API_KEY", "")
    async def submit(self,payload):
        try:
            async with httpx.AsyncClient(timeout=15) as c:
                r=await c.post(self.base+"/invoices",json=payload,headers={"Authorization":f"Bearer {self.key}"})
            if r.status_code==200:
                b=r.json(); return SubmitResult(True,b.get("submission_id"),b.get("status"))
            return SubmitResult(False,error={"http_status":r.status_code,"detail":r.text,"ambiguous":r.status_code==409})
        except (httpx.TimeoutException,httpx.TransportError) as e:
            return SubmitResult(False,unknown=True,error={"type":type(e).__name__,"detail":str(e)})
    async def get_status(self,submission_id):
        async with httpx.AsyncClient(timeout=15) as c:
            r=await c.get(f"{self.base}/invoices/{submission_id}",headers={"Authorization":f"Bearer {self.key}"}); r.raise_for_status(); return r.json()
class ASPBAdapter:
    """ASP B async POST /v2/submissions; status is webhook-only."""
    def __init__(self):
        self.base=os.getenv("ASP_B_BASE_URL","http://localhost:9002").rstrip("/")
        self.key=os.getenv("ASP_B_API_KEY", "")
    async def submit(self,payload):
        try:
            async with httpx.AsyncClient(timeout=15) as c:
                r=await c.post(self.base+"/v2/submissions",json=payload,headers={"Authorization":f"Bearer {self.key}"})
            if r.status_code==202:
                b=r.json(); return SubmitResult(True,b.get("job_id"),b.get("status","QUEUED"))
            return SubmitResult(False,error={"http_status":r.status_code,"detail":r.text})
        except (httpx.TimeoutException,httpx.TransportError) as e:
            return SubmitResult(False,unknown=True,error={"type":type(e).__name__,"detail":str(e)})
