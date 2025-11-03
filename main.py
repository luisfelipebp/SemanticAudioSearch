from fastapi import FastAPI, UploadFile, File, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from faster_whisper import WhisperModel
import chromadb
import os
from process_audio import process_audio_file
from youtube_downloader import baixar_audio_youtube
from fastapi.concurrency import run_in_threadpool 

app = FastAPI(title="Analisador de Áudio com IA API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TEMP_AUDIO_FOLDER = "./temp_audio"
PERSIST_DIR = "./data/chroma_db"
os.makedirs(TEMP_AUDIO_FOLDER, exist_ok=True)
os.makedirs(PERSIST_DIR, exist_ok=True)

print("Carregando modelos e DB... (Isso pode levar um tempo)")
try:
    model_embed = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    model_whisper = WhisperModel("medium", device="cuda", compute_type="float16")
    
    chroma = chromadb.PersistentClient(path=PERSIST_DIR)
    collection = chroma.get_or_create_collection(name="audio", 
    metadata={"hnsw:space": "cosine"})
    
    print("Modelos e DB carregados. API pronta.")
except Exception as e:
    print(f"Erro fatal ao carregar modelos ou DB: {e}")

class YouTubeRequest(BaseModel):
    url: str


@app.post("/upload_audio")
async def upload_audio(file: UploadFile = File(...)):
    """
        Recebe um áudio, salva e inicia o processamento em segundo plano.
    """
    
    file_path = os.path.join(TEMP_AUDIO_FOLDER, file.filename)
    audio_id = os.path.splitext(file.filename)[0]

    try:
        with open(file_path, "wb") as f:
            f.write(await file.read())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Não foi possível salvar o arquivo: {e}")

    existing = collection.get(where={"audio_id": audio_id})
    if existing and len(existing["ids"]) > 0:
        os.remove(file_path) 
        return {"message": "Esse áudio já foi processado anteriormente."}

    try:
        await run_in_threadpool(
            process_audio_file, 
            file_path, 
            audio_id, 
            model_whisper,
            model_embed,
            collection
        )

        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Arquivo original {file_path} removido após processamento.")
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        print(f"Erro durante o processamento do áudio: {e}")
        raise HTTPException(status_code=500, detail=f"Erro no processamento: {e}")

    return {"message": "Áudio processado e indexado com sucesso!"}


@app.post("/process_youtube")
async def process_youtube(request: YouTubeRequest):
    """
     Recebe um link do YouTube, baixa o áudio e inicia o processamento.
    """
    print(f"Recebida requisição para URL: {request.url}")
    
    try:
        file_path, audio_id = await run_in_threadpool(
            baixar_audio_youtube, 
            request.url, 
            TEMP_AUDIO_FOLDER
        )
        if not file_path or not audio_id:
            raise HTTPException(status_code=500, detail="Falha no download do áudio do YouTube.")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no download: {e}")

    print(f"Áudio baixado: {file_path}, ID: {audio_id}")

    existing = collection.get(where={"audio_id": audio_id})
    if existing and len(existing["ids"]) > 0:
        return {
            "message": "Esse áudio já foi processado anteriormente.",
            "audio_id": audio_id,
            "file_path": file_path
        }

    try:
        await run_in_threadpool(
            process_audio_file, 
            file_path, 
            audio_id, 
            model_whisper,
            model_embed,
            collection
        )
    except Exception as e:
        print(f"Erro durante o processamento do YouTube: {e}")
        raise HTTPException(status_code=500, detail=f"Erro no processamento: {e}")

    return {
        "message": "Áudio processado e indexado com sucesso!",
        "audio_id": audio_id,
        "file_path": file_path
    }

@app.get("/search")
def search(query: str = Query(..., description="Pergunta em linguagem natural"),
           audio_id: str = Query(..., description="O nome do arquivo de áudio original para filtrar")):
    """Busca semântica nos trechos do áudio"""
    
    base_audio_id = os.path.splitext(audio_id)[0] 
    
    query_embedding = model_embed.encode([query])
    
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=3,
        where={"audio_id": base_audio_id},
        include=["metadatas", "documents", "distances"]
    )

    response = []
    DISTANCE_THRESHOLD = 0.6
    if results["ids"]:
        for i in range(len(results["ids"][0])):
            distance = results["distances"][0][i]
            
            if distance < DISTANCE_THRESHOLD:
                response.append({
                    "id": results["ids"][0][i],
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": distance 
                })
    return {"query": query, "results": response}


@app.get("/get_transcription")
def get_transcription(audio_id: str = Query(..., description="O nome do arquivo de áudio original")):
    """Busca transcrição completa do áudio"""
    base_audio_id = os.path.splitext(audio_id)[0]

    results = collection.get(
        where={"audio_id": base_audio_id},
        include=["documents", "metadatas"]
    )

    if not results["ids"]:
        return {"query": audio_id, "results": []}

    combined_results = []
    for i in range(len(results["ids"])):
        combined_results.append({
            "id": results["ids"][i],
            "text": results["documents"][i],
            "metadata": results["metadatas"][i]
        })

    sorted_results = sorted(combined_results, key=lambda r: r['metadata']['start'])

    return {"query": audio_id, "results": sorted_results}