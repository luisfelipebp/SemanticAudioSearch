import os
import yt_dlp

def baixar_audio_youtube(url_do_video: str, pasta_saida: str):
    """
    Baixa o áudio do YouTube no formato .m4a.
    """
    
    try:
        info_opts = {'quiet': True, 'noplaylist': True}
        with yt_dlp.YoutubeDL(info_opts) as ydl:
            info = ydl.extract_info(url_do_video, download=False)
            audio_id = info.get('title', 'audio_desconhecido')
            nome_arquivo_seguro = "".join([c if c.isalnum() else "_" for c in audio_id])
    except Exception as e:
        print(f"Erro ao obter informações do vídeo: {e}")
        return None, None

    caminho_final_arquivo = os.path.join(pasta_saida, f"{nome_arquivo_seguro}.m4a")

    ydl_opts = {
        'format': 'bestaudio/best', 
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'm4a',
            'preferredquality': '192', 
        }],
        'outtmpl': os.path.join(pasta_saida, f"{nome_arquivo_seguro}.%(ext)s"), 
        'noplaylist': True,
        'quiet': True,
    }

    try:
        print(f"Baixando e convertendo '{audio_id}' para .m4a...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url_do_video])
        
        print(f"Download concluído: {caminho_final_arquivo}")
        return caminho_final_arquivo, audio_id

    except Exception as e:
        print(f"Ocorreu um erro no download: {e}")
        return None, None