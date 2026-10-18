from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from app.agents.formatter import format_answer
from app.agents.orchestrator import OrchestratorAgent
from app.agents.retrieval import MultimodalRetrievalAgent
from app.config import get_settings
from app.services.store import EvidenceStore


settings = get_settings()
store = EvidenceStore()
orchestrator = OrchestratorAgent(MultimodalRetrievalAgent(store.index), top_k=settings.top_k)

app = FastAPI(title="EvidenceLens", version="0.1.0", description="Inspectable multimodal evidence intelligence")


class QueryRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)


@app.get("/health")
def health() -> dict[str, object]:
    return {"status": "ok", "service": "evidencelens", "evidence_count": len(store.evidence()), "mock_mode": settings.mock_mode}


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return """<!doctype html><html><head><title>EvidenceLens</title><meta name='viewport' content='width=device-width,initial-scale=1'>
    <style>body{font:16px system-ui;max-width:1000px;margin:30px auto;padding:0 18px;color:#172033;background:#f6f8fb}main{background:white;padding:28px;border-radius:18px;box-shadow:0 8px 30px #17203315}h1{margin:0;color:#3157d5}textarea{width:100%;min-height:90px;margin:10px 0;padding:10px}button{background:#3157d5;color:white;border:0;padding:11px 18px;border-radius:8px;cursor:pointer}.card{border:1px solid #dde3ee;border-radius:10px;padding:14px;margin:10px 0}.muted{color:#667085}.warn{color:#a15c00}</style></head>
    <body><main><h1>EvidenceLens</h1><p class='muted'>Ask questions across documents, images, charts, and tables — with inspectable evidence.</p>
    <form id='upload'><input type='file' id='files' multiple accept='.pdf,.txt,.md,.csv,.xlsx,.png,.jpg,.jpeg'><button>Process evidence</button></form><div id='status'></div>
    <hr><form id='query'><textarea id='question'>Which category changed the most, and does the chart agree with the table?</textarea><button>Ask EvidenceLens</button></form><section id='answer'></section></main>
    <script>const s=document.querySelector('#status'),a=document.querySelector('#answer');document.querySelector('#upload').onsubmit=async e=>{e.preventDefault();let f=new FormData();for(const x of document.querySelector('#files').files)f.append('files',x);s.textContent='Processing...';let r=await fetch('/api/upload',{method:'POST',body:f});s.textContent=JSON.stringify(await r.json())};document.querySelector('#query').onsubmit=async e=>{e.preventDefault();a.innerHTML='Retrieving and verifying...';let r=await fetch('/api/query',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({question:document.querySelector('#question').value})});let d=await r.json();a.innerHTML='<div class="card"><b>Answer</b><p>'+d.answer+'</p><p>Confidence: '+d.confidence+' | Verification: '+d.verification_status+'</p></div><div class="card"><b>Workflow</b><ul>'+d.workflow_events.map(x=>'<li>'+x.label+': '+x.detail+'</li>').join('')+'</ul></div><div class="card"><b>Evidence</b>'+d.citations.map(x=>'<p>'+x.label+'</p>').join('')+'</div>'}</script></body></html>"""


@app.post("/api/upload")
async def upload(files: list[UploadFile] = File(...)) -> dict[str, object]:
    max_bytes = settings.max_upload_mb * 1024 * 1024
    payloads: list[tuple[str, bytes]] = []
    errors: list[str] = []
    for upload_file in files:
        content = await upload_file.read()
        if len(content) > max_bytes:
            errors.append(f"{upload_file.filename}: exceeds {settings.max_upload_mb} MB limit")
            continue
        payloads.append((upload_file.filename or "unnamed", content))
    if not payloads and errors:
        raise HTTPException(status_code=413, detail=errors)
    result = store.ingest_files(payloads)
    return {"files": result.files, "evidence_count": len(result.evidence), "errors": errors + result.errors}


@app.post("/api/query")
def query(request: QueryRequest):
    plan, evidence, events = orchestrator.run(request.question)
    return format_answer(request.question, evidence, events).model_dump(mode="json")


@app.get("/api/evidence")
def evidence():
    return {"items": [item.model_dump(mode="json") for item in store.evidence()], "files": store.files, "errors": store.errors}


@app.post("/api/reset")
def reset() -> dict[str, str]:
    store.reset()
    return {"status": "reset"}
