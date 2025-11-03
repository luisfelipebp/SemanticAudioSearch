import streamlit as st
import requests
import time
import os

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Analisador de Áudio com IA", layout="wide")
st.title("Analisador de Áudio com IA")

st.write("Envie um áudio (upload ou link do YouTube) para análise.")

if 'start_time' not in st.session_state:
    st.session_state.start_time = 0
if 'audio_bytes' not in st.session_state:
    st.session_state.audio_bytes = None
if 'upload_processed' not in st.session_state:
    st.session_state.upload_processed = False
if 'audio_filename' not in st.session_state:
    st.session_state.audio_filename = ""
if 'processed_source' not in st.session_state:
    st.session_state.processed_source = None
if 'active_audio_id' not in st.session_state:
    st.session_state.active_audio_id = None
if 'active_source_type' not in st.session_state:
    st.session_state.active_source_type = None

tab1, tab2 = st.tabs(["Upload de Arquivo", "Link do YouTube"])

with tab1:
    uploaded_file = st.file_uploader("Selecione o arquivo de áudio", type=["m4a", "mp3"])

    if uploaded_file is not None:
        if st.button("Enviar e Processar Upload"):
            st.session_state.audio_bytes = uploaded_file.read()
            st.session_state.start_time = 0
            st.session_state.audio_filename = uploaded_file.name
            st.session_state.upload_processed = False
            st.session_state.processed_source = uploaded_file.name

            with st.spinner("Processando o áudio... isso pode levar alguns minutos"):
                files_payload = {
                    "file": (uploaded_file.name, st.session_state.audio_bytes, uploaded_file.type)
                }
                try:
                    response = requests.post(f"{API_URL}/upload_audio", files=files_payload)

                    if response.status_code == 200:
                        st.session_state.upload_processed = True
                        st.session_state.active_audio_id = uploaded_file.name
                        st.session_state.active_source_type = "upload"
                        st.success("Áudio processado e indexado com sucesso!")
                    else:
                        st.session_state.upload_processed = False
                        st.error(f"Erro ao processar o áudio: {response.status_code} {response.text}")
                except requests.exceptions.RequestException as e:
                    st.session_state.upload_processed = False
                    st.error(f"Erro de conexão com a API: {e}")

            st.rerun()

with tab2:
    youtube_url = st.text_input("Cole o link do YouTube aqui:")

    if st.button("Processar Link do YouTube"):
        if youtube_url and youtube_url != st.session_state.processed_source:
            with st.spinner("Baixando e processando áudio do YouTube..."):
                try:
                    payload = {"url": youtube_url}
                    response = requests.post(f"{API_URL}/process_youtube", json=payload)

                    if response.status_code == 200:
                        data = response.json()
                        audio_id = data.get("audio_id")
                        file_path = data.get("file_path")

                        if file_path and os.path.exists(file_path):
                            with open(file_path, "rb") as f:
                                audio_data = f.read()
                            os.remove(file_path)

                            st.session_state.audio_bytes = audio_data
                            st.session_state.audio_filename = audio_id
                            st.session_state.upload_processed = True
                            st.session_state.start_time = 0
                            st.session_state.processed_source = youtube_url
                            st.session_state.active_audio_id = audio_id
                            st.session_state.active_source_type = "youtube"

                            st.success(f"Áudio '{audio_id}' processado com sucesso!")
                            st.rerun()
                        else:
                            st.error(f"API processou, mas não foi possível encontrar o arquivo temporário.")
                            st.session_state.upload_processed = False
                    else:
                        st.error(f"Erro ao processar o link: {response.status_code} {response.text}")
                        st.session_state.upload_processed = False
                except requests.exceptions.RequestException as e:
                    st.error(f"Erro de conexão com a API: {e}")
                    st.session_state.upload_processed = False
        elif not youtube_url:
            st.warning("Por favor, insira um link do YouTube.")
        elif youtube_url == st.session_state.processed_source:
            st.info("Este link já foi processado. Os resultados estão abaixo.")

if st.session_state.audio_bytes is not None:
    if st.session_state.active_source_type:
        tipo = "Upload" if st.session_state.active_source_type == "upload" else "YouTube"

    st.write("### Player de Áudio")
    st.audio(st.session_state.audio_bytes, start_time=st.session_state.start_time)
    st.divider()

    if st.session_state.upload_processed:
        if st.button("Ver Transcrição Completa"):
            params = {"audio_id": st.session_state.active_audio_id}

            with st.spinner("Buscando transcrição..."):
                try:
                    res_transc = requests.get(f"{API_URL}/get_transcription", params=params)
                    if res_transc.status_code == 200:
                        results = res_transc.json().get("results", [])
                        st.subheader("Transcrição Completa")
                        if not results:
                            st.write("Nenhuma transcrição encontrada para este áudio.")
                        else:
                            full_transcription = " ".join([r['text'] for r in results])
                            st.text_area("Transcrição:", full_transcription, height=300)
                    else:
                        st.error(f"Erro ao buscar a transcrição: {res_transc.status_code}")
                except requests.exceptions.RequestException as e:
                    st.error(f"Erro de conexão com a API: {e}")

        st.divider()

        st.subheader("Buscar no conteúdo do áudio")
        query = st.text_input("Digite sua pergunta:")

        if query:
            with st.spinner("Buscando nos trechos..."):
                try:
                    params = {
                        "query": query,
                        "audio_id": st.session_state.active_audio_id
                    }
                    res = requests.get(f"{API_URL}/search", params=params)
                    if res.status_code == 200:
                        results = res.json().get("results", [])
                        if not results:
                            st.write("Nenhum resultado encontrado para esta busca.")
                        else:
                            st.write("Resultados encontrados:")
                            st.caption("Resultados baseados no significado (busca semântica), não apenas em palavras-chave exatas.")
                            for i, r in enumerate(results):
                                start_s = r['metadata']['start'] / 1000
                                end_s = r['metadata']['end'] / 1000
                                time_label = f"{int(start_s // 60)}:{int(start_s % 60):02d} – {int(end_s // 60)}:{int(end_s % 60):02d}"
                                text_preview = r["text"]

                                with st.expander(f"**{time_label}**"):
                                    st.write(text_preview)
                                    if st.button(f"Ir para {int(start_s)}s", key=f"jump_{i}_{start_s}"):
                                        st.session_state.start_time = int(start_s)
                                        st.rerun()
                    else:
                        st.error(f"Erro na busca: {res.status_code}")
                except requests.exceptions.RequestException as e:
                    st.error(f"Erro de conexão com a API: {e}")

    elif st.session_state.audio_filename and not st.session_state.upload_processed:
        st.error("O processamento do áudio falhou. Tente enviar novamente.")
else:
    st.info("Por favor, selecione uma fonte de áudio acima para começar.")