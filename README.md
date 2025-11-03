# Analisador de Áudio com IA

Um aplicativo **full-stack** que permite enviar arquivos de áudio (ou links do YouTube), **transcrevê-los automaticamente** e **realizar buscas semânticas** dentro do conteúdo.  
A interface também permite **pular diretamente para o trecho do áudio** onde sua busca foi encontrada.

---

## Funcionalidades

- **Upload de Áudio:** Envie arquivos `.mp3` ou `.m4a` diretamente pela interface.  
- **Integração com YouTube:** Cole um link de vídeo e o sistema baixa e processa o áudio automaticamente.  
- **Transcrição Automática:** Utiliza o modelo **medium** do `faster-whisper` para gerar transcrições de alta qualidade em português.  
- **Busca Semântica:** Pesquise por significado — não apenas por palavras exatas.  
- **Player Interativo:** Clique em um resultado e vá direto para o trecho correspondente do áudio.  
- **Visualização da Transcrição:** Veja a transcrição completa do áudio processado.  
- **Persistência de Dados:** As transcrições e embeddings são armazenadas localmente com **ChromaDB**, evitando reprocessamentos desnecessários.

---

## Arquitetura do Projeto

O sistema é composto por três principais módulos:

### 1. **Frontend – Streamlit (`dashboard.py`)**
Interface web interativa que:
- Recebe uploads de áudio ou links do YouTube.
- Exibe os resultados de busca e player de áudio.
- Se comunica com o backend via requisições HTTP (API REST).

### 2. **Backend – FastAPI (`main.py`)**
API que:
- Processa uploads e links recebidos.
- Gerencia os modelos de IA (Whisper e SentenceTransformer).
- Interage com o banco de dados vetorial (ChromaDB).
- Expõe endpoints para transcrição e busca semântica.

### 3. **Processamento – (`process_audio.py`)**
Responsável por:
- Dividir o áudio em **chunks de 60 segundos** usando `pydub`.
- Transcrever cada trecho com `faster-whisper`.
- Gerar embeddings de texto com `sentence-transformers`.
- Armazenar textos, vetores e metadados no ChromaDB.

---

## Tecnologias Utilizadas

| Categoria | Tecnologias |
|------------|--------------|
| **Frontend** | Streamlit |
| **Backend** | FastAPI, Uvicorn |
| **Transcrição (ASR)** | faster-whisper |
| **Embeddings de Texto** | sentence-transformers (`paraphrase-multilingual-MiniLM-L12-v2`) |
| **Banco Vetorial** | ChromaDB |
| **Áudio** | pydub |
| **Download YouTube** | yt-dlp |

---

## Instalação e Execução

### Pré-requisitos
- Python 3.9+
- FFmpeg (necessário para o `pydub`)
- (Opcional, mas recomendado) GPU NVIDIA com suporte CUDA

---

### Clone o Repositório

```bash
git clone https://github.com/luisfelipebp/SemanticAudioSearch.git
cd SemanticAudioSearch
```

### Crie e Ative um Ambiente Virtual

Crie um ambiente isolado para o projeto:

```bash
python -m venv venv
```

Ative o ambiente:

```
# Windows
.\venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### Instale as Dependências

```bash
pip install -r requirements.txt
```

#### Aviso sobre GPU/CPU

O modelo Whisper está configurado para usar CUDA por padrão.
Se você não possui uma GPU NVIDIA, altere a linha correspondente em main.py para usar CPU:

```bash
# Em main.py
model_whisper = WhisperModel("medium", device="cpu", compute_type="int8")
```

### Execute a Aplicação

Você precisará de dois terminais para rodar o projeto:

#### Terminal 1 – Backend (FastAPI)
```bash
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

#### Terminal 2 – Frontend (Streamlit)
```bash
streamlit run app.py
```

### Estrutura de Arquivos

```
├── dashboard.py            # Frontend (Streamlit)
├── main.py                 # Backend (FastAPI)
├── process_audio.py        # Lógica de processamento e embeddings
├── youtube_downloader.py   # Download e extração de áudio do YouTube
├── requirements.txt        # Dependências do projeto
├── data/
│   └── chroma_db/          # Banco de dados vetorial (gerado em runtime)
└── temp_audio/             # Áudios temporários baixados ou enviados
```


