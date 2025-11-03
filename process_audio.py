import os
import math
from pydub import AudioSegment
import tempfile
import shutil

jargon_prompt = ""

def process_audio_file(audio_file: str, audio_id: str, model_whisper, model_embed, collection):
    """
    Função de processamento refatorada.
    Recebe os modelos e a coleção como argumentos.
    """
    
    temp_dir = tempfile.mkdtemp()
    folder_output = temp_dir
    chunk_ms = 60 * 1000

    print(f"Processando {audio_id} no diretório temporário: {temp_dir}")
    
    try:
        print("Dividindo o áudio...")
        audio = AudioSegment.from_file(audio_file)
        duration_total_ms = len(audio)
        num_chunks = math.ceil(duration_total_ms / chunk_ms)

        for i in range(num_chunks):
            start = i * chunk_ms
            end = min((i + 1) * chunk_ms, duration_total_ms)
            chunk = audio[start:end]
            chunk.export(f"{folder_output}/chunk_{i+1}.mp3", format="mp3")

        print(f"{num_chunks} pedaços criados.")

        print("Transcrevendo áudio com Whisper...")
        transcriptions = []
        files = sorted(
            [f for f in os.listdir(folder_output) if f.endswith(".mp3")],
            key=lambda x: int(x.split("_")[1].split(".")[0])
        )

        for i, file in enumerate(files):
            path = os.path.join(folder_output, file)
            segments, info = model_whisper.transcribe(
                path, 
                initial_prompt=jargon_prompt,
                language="pt"
            )
            text_result = "".join([segment.text for segment in segments])
            transcriptions.append({
                "id": f"{audio_id}_{i}",
                "text": text_result.strip(),
                "start": i * chunk_ms,
                "end": (i + 1) * chunk_ms,
            })

        print(f"{len(transcriptions)} transcrições obtidas.")
        transcriptions.sort(key=lambda x: x["start"])

        print("Gerando embeddings e indexando...")
        texts = [t["text"] for t in transcriptions]
        ids = [t["id"] for t in transcriptions]
        metadatas = [{"start": t["start"], "end": t["end"], "audio_id": audio_id} for t in transcriptions]
        
        embeddings = model_embed.encode(texts)

        collection.add(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)
        print("Banco vetorial atualizado!")

    except Exception as e:
        print(f"Falha ao processar o arquivo {audio_id}: {e}")
    
    finally:
        if os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                print(f"Diretório temporário {temp_dir} limpo.")
            except Exception as e:
                print(f"Erro ao limpar diretório temporário {temp_dir}: {e}")