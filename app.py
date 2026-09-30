import streamlit as st
import streamlit.components.v1 as components
import requests
import json

# Configuração da página
st.set_page_config(
    page_title="Extrator de Links do YouTube",
    page_icon="▶️",
    layout="centered"
)

# Estilização complementar
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .sub-title {
        font-size: 1rem;
        color: #B0B0B0;
        margin-bottom: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Inicialização do estado da sessão (st.session_state)
if "search_results" not in st.session_state:
    st.session_state.search_results = None

if "keyword_input" not in st.session_state:
    st.session_state.keyword_input = ""

# Função para renderizar botão HTML/JS de cópia para a área de transferência
def render_copy_button(text_to_copy: str):
    escaped_text = json.dumps(text_to_copy)
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            * {{
                box-sizing: border-box;
                margin: 0;
                padding: 0;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            }}
            body {{
                background: transparent;
                display: flex;
                align-items: center;
                height: 100%;
                overflow: hidden;
            }}
            .copy-btn {{
                width: 100%;
                height: 38px;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                background-color: #262730;
                color: #FAFAFA;
                border: 1px solid rgba(250, 250, 250, 0.2);
                border-radius: 8px;
                font-size: 14px;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.2s ease-in-out;
                outline: none;
                user-select: none;
            }}
            .copy-btn:hover {{
                border-color: #FF0000;
                color: #FF0000;
                background-color: #1E1E24;
            }}
            .copy-btn.copied {{
                background-color: #1E3A2F !important;
                border-color: #28a745 !important;
                color: #4cd964 !important;
            }}
        </style>
    </head>
    <body>
        <button id="btn-copy" class="copy-btn" onclick="copyContent()">
            📋 Copiar Todos
        </button>
        <script>
            const textToCopy = {escaped_text};
            function copyContent() {{
                if (navigator.clipboard && window.isSecureContext) {{
                    navigator.clipboard.writeText(textToCopy).then(() => {{
                        setSuccess();
                    }}).catch(err => {{
                        fallbackCopy(textToCopy);
                    }});
                }} else {{
                    fallbackCopy(textToCopy);
                }}
            }}
            function fallbackCopy(text) {{
                const textArea = document.createElement("textarea");
                textArea.value = text;
                textArea.style.position = "fixed";
                textArea.style.left = "-999999px";
                document.body.appendChild(textArea);
                textArea.focus();
                textArea.select();
                try {{
                    document.execCommand('copy');
                    setSuccess();
                }} catch (err) {{
                    console.error('Fallback copy failed', err);
                }}
                document.body.removeChild(textArea);
            }}
            function setSuccess() {{
                const btn = document.getElementById('btn-copy');
                btn.innerText = "✅ Copiado!";
                btn.classList.add('copied');
                setTimeout(() => {{
                    btn.innerText = "📋 Copiar Todos";
                    btn.classList.remove('copied');
                }}, 2000);
            }}
        </script>
    </body>
    </html>
    """
    components.html(html_code, height=45)

# Título da Aplicação
st.markdown('<div class="main-title">🎥 Extrator de Links do YouTube</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Busque vídeos por palavra-chave e obtenha links prontos para cópia em massa.</div>', unsafe_allow_html=True)

# Obter a chave da API a partir do st.secrets
api_key = st.secrets.get("YOUTUBE_API_KEY", "")

# Verificação se a chave da API foi configurada
if not api_key or api_key == "SUA_CHAVE_API_AQUI":
    st.warning(
        "⚠️ **Chave da API não configurada!**\n\n"
        "Configure sua chave no arquivo `.streamlit/secrets.toml`:\n"
        "```toml\n"
        'YOUTUBE_API_KEY = "sua_chave_real_aqui"\n'
        "```"
    )

# Campo de entrada para a palavra-chave
keyword = st.text_input(
    label="Palavra-chave ou termo de pesquisa:",
    placeholder="Ex: inteligência artificial, podcast de tecnologia, lofi hip hop...",
    help="Digite o termo que deseja pesquisar no YouTube para extrair os links dos vídeos.",
    key="keyword_input"
)

# Botão de busca
search_clicked = st.button("Buscar Links", type="primary", use_container_width=True)

if search_clicked:
    if not keyword.strip():
        st.error("Por favor, insira uma palavra-chave para realizar a busca.")
    elif not api_key or api_key == "SUA_CHAVE_API_AQUI":
        st.error("Por favor, configure a chave de API em `.streamlit/secrets.toml` antes de buscar.")
    else:
        with st.spinner("Consultando a YouTube Data API v3..."):
            endpoint = "https://www.googleapis.com/youtube/v3/search"
            params = {
                "part": "id,snippet",
                "q": keyword.strip(),
                "type": "video",
                "maxResults": 50,
                "key": api_key
            }

            try:
                response = requests.get(endpoint, params=params, timeout=15)
                data = response.json()

                if response.status_code == 200:
                    items = data.get("items", [])
                    
                    video_links = []
                    video_details = []

                    for item in items:
                        video_id = item.get("id", {}).get("videoId")
                        if video_id:
                            url = f"https://www.youtube.com/watch?v={video_id}"
                            title = item.get("snippet", {}).get("title", "Sem título")
                            channel = item.get("snippet", {}).get("channelTitle", "Canal desconhecido")
                            
                            video_links.append(url)
                            video_details.append({"title": title, "channel": channel, "url": url})

                    if video_links:
                        links_text = "\n".join(video_links)
                        st.session_state.search_results = {
                            "keyword": keyword.strip(),
                            "video_links": video_links,
                            "video_details": video_details,
                            "links_text": links_text
                        }
                    else:
                        st.session_state.search_results = None
                        st.info("Nenhum vídeo encontrado para essa palavra-chave.")

                else:
                    st.session_state.search_results = None
                    error_info = data.get("error", {})
                    error_message = error_info.get("message", "Erro desconhecido ao consultar a API.")
                    error_code = error_info.get("code", response.status_code)
                    
                    st.error(f"❌ **Erro na requisição ({error_code})**: {error_message}")
                    if error_code == 403:
                        st.info("💡 **Dica**: Verifique se a YouTube Data API v3 está habilitada no seu Google Cloud Console ou se a cota diária foi excedida.")
                    elif error_code == 400:
                        st.info("💡 **Dica**: Verifique se a chave de API inserida no `secrets.toml` é válida.")

            except requests.exceptions.Timeout:
                st.error("⏱️ Tempo limite excedido ao conectar com a YouTube API. Tente novamente.")
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Ocorreu um erro de conexão: {str(e)}")

# Exibição dos resultados a partir do st.session_state
if st.session_state.search_results:
    results = st.session_state.search_results
    keyword_used = results["keyword"]
    video_links = results["video_links"]
    video_details = results["video_details"]
    links_text = results["links_text"]

    st.success(f"Foram encontrados **{len(video_links)}** vídeos para a busca: *'{keyword_used}'*")
    
    # Text area para cópia em massa
    st.subheader("📋 Links extraídos (prontos para cópia)")
    st.text_area(
        label="Links dos Vídeos (1 por linha):",
        value=links_text,
        height=280,
        help="Clique dentro da caixa, selecione tudo (Ctrl+A / Cmd+A) e copie (Ctrl+C / Cmd+C)."
    )

    # 3 Botões alinhados horizontalmente com st.columns
    col1, col2, col3 = st.columns(3)

    with col1:
        # Botão 1: Copiar Todos via HTML/JS
        render_copy_button(links_text)

    with col2:
        # Botão 2: Download em .txt
        st.download_button(
            label="💾 Baixar (.txt)",
            data=links_text,
            file_name=f"youtube_links_{keyword_used.replace(' ', '_')}.txt",
            mime="text/plain",
            use_container_width=True
        )

    with col3:
        # Botão 3: Limpar Estado da Aplicação
        if st.button("🗑️ Limpar", use_container_width=True):
            st.session_state.search_results = None
            st.session_state.keyword_input = ""
            st.rerun()

    # Exibição dos detalhes dos vídeos encontrados
    with st.expander("🔍 Ver detalhes dos vídeos encontrados"):
        for idx, detail in enumerate(video_details, 1):
            st.markdown(f"**{idx}. [{detail['title']}]({detail['url']})** — *{detail['channel']}*")
