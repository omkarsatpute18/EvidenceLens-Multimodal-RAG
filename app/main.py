from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel, Field

from app.agents.formatter import format_answer
from app.agents.orchestrator import OrchestratorAgent
from app.agents.retrieval import MultimodalRetrievalAgent
from app.config import get_settings
from app.services.model import build_multimodal_analyzer
from app.services.store import EvidenceStore


settings = get_settings()
analyzer = build_multimodal_analyzer(settings)
store = EvidenceStore(analyzer=analyzer)
orchestrator = OrchestratorAgent(MultimodalRetrievalAgent(store.index), top_k=settings.top_k)

app = FastAPI(title="EvidenceLens", version="0.2.0", description="Inspectable multimodal evidence intelligence")


class QueryRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)


@app.get("/health")
def health() -> dict[str, object]:
    return {
        "status": "ok",
        "service": "evidencelens",
        "version": app.version,
        "evidence_count": len(store.evidence()),
        "mock_mode": settings.mock_mode,
        "analyzer": type(analyzer).__name__,
    }


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return """<!doctype html><html><head><title>EvidenceLens</title><meta name='viewport' content='width=device-width,initial-scale=1'>
    <style>body{font:16px system-ui;max-width:1100px;margin:30px auto;padding:0 18px;color:#172033;background:#f6f8fb}main{background:white;padding:28px;border-radius:18px;box-shadow:0 8px 30px #17203315}h1{margin:0;color:#3157d5}h2{font-size:19px;margin:0 0 8px}textarea{width:100%;min-height:90px;margin:10px 0;padding:10px;border:1px solid #cfd7e6;border-radius:8px;box-sizing:border-box}button{background:#3157d5;color:white;border:0;padding:11px 18px;border-radius:8px;cursor:pointer;margin:4px 4px 4px 0}.secondary{background:#64748b}.card{border:1px solid #dde3ee;border-radius:10px;padding:14px;margin:10px 0}.muted{color:#667085}.warn{color:#a15c00;background:#fff7ed;padding:8px;border-radius:8px}.ok{color:#176b45}.chips span{display:inline-block;background:#eef2ff;padding:4px 8px;border-radius:999px;margin:3px;font-size:13px}.evidence{background:#fbfcfe}.evidence img{max-width:100%;max-height:260px;border-radius:8px;border:1px solid #dde3ee}.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}@media(max-width:750px){.grid{grid-template-columns:1fr}}</style></head>
    <body><main><h1>EvidenceLens</h1><p class='muted'>Ask questions across documents, images, charts, and tables — with inspectable evidence.</p>
    <section class='card'><h2>1. Build an evidence bundle</h2><form id='upload'><input type='file' id='files' multiple accept='.pdf,.txt,.md,.csv,.xlsx,.png,.jpg,.jpeg'><br><button>Process evidence</button><button type='button' id='reset' class='secondary'>New bundle</button></form><div id='status' aria-live='polite'></div></section>
    <section class='card'><h2>2. Ask an evidence-grounded question</h2><div id='examples' class='chips'></div><form id='query'><textarea id='question'>Which region had the largest decline, what evidence supports this conclusion, and does the chart agree with the table?</textarea><button>Ask EvidenceLens</button></form></section>
    <section id='answer' aria-live='polite'></section></main>
    <script>
    const statusBox=document.querySelector('#status'),answerBox=document.querySelector('#answer'),questionBox=document.querySelector('#question');
    const examples=['Which region changed the most?','Does the chart agree with the table?','What evidence supports the conclusion?','What information is missing?','Are any sources inconsistent?'];
    const make=(tag,text='',className='')=>{const node=document.createElement(tag);node.textContent=text;if(className)node.className=className;return node};
    const clear=node=>{while(node.firstChild)node.removeChild(node.firstChild)};
    examples.forEach(value=>{const button=make('button',value);button.type='button';button.onclick=()=>{questionBox.value=value};document.querySelector('#examples').appendChild(button)});
    function renderUpload(data){clear(statusBox);const summary=make('p',`Processed ${data.files.length} file(s), extracted ${data.evidence_count} evidence item(s).`, 'ok');statusBox.appendChild(summary);const files=make('div');data.files.forEach(name=>files.appendChild(make('span',name,'chips')));statusBox.appendChild(files);if(data.items&&data.items.length){const modes=make('div','');data.items.forEach(item=>{const label=item.content_type+(item.analysis_mode?' · '+item.analysis_mode:'');modes.appendChild(make('span',label,'chips'))});statusBox.appendChild(modes)}if(data.errors&&data.errors.length){const warning=make('p',data.errors.join(' | '),'warn');statusBox.appendChild(warning)}}
    function renderAnswer(data){clear(answerBox);const grid=make('div','');grid.className='grid';const answer=make('article','', 'card');answer.appendChild(make('h2','Answer'));answer.appendChild(make('p',data.answer));answer.appendChild(make('p',`Confidence: ${Math.round(Number(data.confidence||0)*100)}% · Verification: ${data.verification_status}`));grid.appendChild(answer);const workflow=make('article','', 'card');workflow.appendChild(make('h2','Workflow'));const steps=make('ul');(data.workflow_events||[]).forEach(event=>steps.appendChild(make('li',`${event.label}: ${event.detail}`)));workflow.appendChild(steps);grid.appendChild(workflow);answerBox.appendChild(grid);if(data.contradictions&&data.contradictions.length){const conflicts=make('article','', 'card warn');conflicts.appendChild(make('h2','Possible inconsistencies'));data.contradictions.forEach(value=>conflicts.appendChild(make('p',value)));answerBox.appendChild(conflicts)}if(data.limitations&&data.limitations.length){const limits=make('article','', 'card');limits.appendChild(make('h2','Limitations'));data.limitations.forEach(value=>limits.appendChild(make('p',value)));answerBox.appendChild(limits)}const evidenceById=new Map((data.evidence_items||[]).map(item=>[item.evidence_id,item]));const evidence=make('article','', 'card');evidence.appendChild(make('h2','Inspect evidence'));(data.citations||[]).forEach(citation=>{const item=evidenceById.get(citation.evidence_id);const card=make('div','', 'card evidence');card.appendChild(make('strong',citation.label));if(item){card.appendChild(make('p',item.text_content||'No extracted text.'));card.appendChild(make('p',`Type: ${item.content_type} · Extraction confidence: ${item.extraction_confidence} · Retrieval score: ${item.retrieval_score??'n/a'}`));if(item.structured_content&&Object.keys(item.structured_content).length)card.appendChild(make('pre',JSON.stringify(item.structured_content,null,2)));if(item.metadata&&item.metadata.retrieval_trace)card.appendChild(make('pre',`Retrieval trace: ${JSON.stringify(item.metadata.retrieval_trace)}`));if(item.metadata&&item.metadata.analysis_warning)card.appendChild(make('p',item.metadata.analysis_warning,'warn'));if(item.image_reference&&item.image_reference.startsWith('/api/evidence/')){const image=document.createElement('img');image.src=item.image_reference;image.alt='Evidence image preview';card.appendChild(image)}}evidence.appendChild(card)});answerBox.appendChild(evidence)}
    document.querySelector('#upload').onsubmit=async event=>{event.preventDefault();const form=new FormData();for(const file of document.querySelector('#files').files)form.append('files',file);statusBox.textContent='Processing evidence…';try{const response=await fetch('/api/upload',{method:'POST',body:form});const data=await response.json();if(!response.ok){statusBox.textContent=Array.isArray(data.detail)?data.detail.join(' | '):(data.detail||'Upload failed.');return}renderUpload(data)}catch(error){statusBox.textContent='Upload failed. Please try again.'}};
    document.querySelector('#query').onsubmit=async event=>{event.preventDefault();answerBox.textContent='Retrieving and verifying…';try{const response=await fetch('/api/query',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({question:questionBox.value})});const data=await response.json();if(!response.ok){answerBox.textContent=data.detail||'Query failed.';return}renderAnswer(data)}catch(error){answerBox.textContent='Query failed. Please try again.'}};
    document.querySelector('#reset').onclick=async()=>{await fetch('/api/reset',{method:'POST'});clear(statusBox);clear(answerBox);document.querySelector('#files').value='';};
    </script></body></html>"""


@app.post("/api/upload")
async def upload(files: list[UploadFile] = File(...)) -> dict[str, object]:
    max_bytes = settings.max_upload_mb * 1024 * 1024
    payloads: list[tuple[str, bytes]] = []
    errors: list[str] = []
    for upload_file in files:
        content = await upload_file.read(max_bytes + 1)
        if len(content) > max_bytes:
            errors.append(f"{upload_file.filename}: exceeds {settings.max_upload_mb} MB limit")
            continue
        payloads.append((upload_file.filename or "unnamed", content))
    if not payloads and errors:
        raise HTTPException(status_code=413, detail=errors)
    result = store.ingest_files(payloads)
    return {
        "files": result.files,
        "evidence_count": len(result.evidence),
        "errors": errors + result.errors,
        "items": [
            {
                "evidence_id": item.evidence_id,
                "source_file": item.source_file,
                "content_type": item.content_type.value,
                "analysis_mode": item.metadata.get("analysis_mode"),
                "warning": item.metadata.get("analysis_warning"),
            }
            for item in result.evidence
        ],
    }


@app.post("/api/query")
def query(request: QueryRequest):
    plan, evidence, events = orchestrator.run(request.question)
    return format_answer(request.question, evidence, events).model_dump(mode="json")


@app.get("/api/evidence")
def evidence():
    return {"items": [item.model_dump(mode="json") for item in store.evidence()], "files": store.files, "errors": store.errors}


@app.get("/api/evidence/{evidence_id}/asset")
def evidence_asset(evidence_id: str) -> Response:
    asset = store.asset(evidence_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="Evidence asset not found")
    content, media_type = asset
    return Response(content=content, media_type=media_type, headers={"Content-Disposition": "inline"})


@app.post("/api/reset")
def reset() -> dict[str, str]:
    store.reset()
    return {"status": "reset"}
