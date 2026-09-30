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

# Mapeamento de Países para ISO 3166-1 alpha-2
COUNTRY_OPTIONS = {
    "Qualquer País": "",
    "Brasil (BR)": "BR",
    "Estados Unidos (US)": "US",
    "Portugal (PT)": "PT",
    "Reino Unido (GB)": "GB",
    "Espanha (ES)": "ES",
    "Canadá (CA)": "CA",
    "França (FR)": "FR",
    "Alemanha (DE)": "DE",
    "Itália (IT)": "IT",
    "México (MX)": "MX",
    "Argentina (AR)": "AR",
    "Japão (JP)": "JP",
    "Austrália (AU)": "AU",
    "Índia (IN)": "IN"
}

# Mapeamento de Idiomas para ISO 639-1
LANGUAGE_OPTIONS = {
    "Qualquer Idioma": "",
    "Português (pt)": "pt",
    "Inglês (en)": "en",
    "Japonês (ja)": "ja",
    "Espanhol (es)": "es",
    "Francês (fr)": "fr",
    "Alemão (de)": "de",
    "Italiano (it)": "it"
}

# Inicialização do estado da sessão (st.session_state)
if "search_results" not in st.session_state:
    st.session_state.search_results = None

if "keyword_input" not in st.session_state:
    st.session_state.keyword_input = ""

if "country_input" not in st.session_state:
    st.session_state.country_input = "Qualquer País"

if "language_input" not in st.session_state:
    st.session_state.language_input = "Qualquer Idioma"

if "min_views_input" not in st.session_state:
    st.session_state.min_views_input = 0

if "min_subs_input" not in st.session_state:
    st.session_state.min_subs_input = 0

# Função para formatação compacta de números (ex: 50K, 1.2M)
def format_compact_number(num: int) -> str:
    if num >= 1_000_000:
        val = num / 1_000_000
        return f"{val:.1f}M".replace(".0M", "M")
    elif num >= 1_000:
        val = num / 1_000
        return f"{val:.1f}K".replace(".0K", "K")
    return str(num)

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
st.markdown('<div class="sub-title">Busque vídeos por palavra-chave, país, idioma e métricas mínimas, e copie links em massa.</div>', unsafe_allow_html=True)

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

# Linha 1 de Filtros: País e Idioma do Vídeo
col_country, col_lang = st.columns(2)

with col_country:
    selected_country_label = st.selectbox(
        label="País da Pesquisa:",
        options=list(COUNTRY_OPTIONS.keys()),
        key="country_input",
        help="Filtra a pesquisa para vídeos populares e relevantes no país selecionado (regionCode)."
    )

with col_lang:
    selected_language_label = st.selectbox(
        label="Idioma do Vídeo:",
        options=list(LANGUAGE_OPTIONS.keys()),
        key="language_input",
        help="Prioriza conteúdos no idioma selecionado, evitando que conteúdos globais dominem o resultado (relevanceLanguage)."
    )

# Linha 2 de Filtros: Visualizações e Inscritos Mínimos
col_views, col_subs = st.columns(2)

with col_views:
    min_views = st.number_input(
        label="Visualizações mínimas:",
        min_value=0,
        value=0,
        step=1000,
        key="min_views_input",
        help="Filtra apenas os vídeos com visualizações iguais ou maiores que este valor (0 = todos)."
    )

with col_subs:
    min_subs = st.number_input(
        label="Inscritos mínimos:",
        min_value=0,
        value=0,
        step=1000,
        key="min_subs_input",
        help="Filtra apenas canais com inscritos iguais ou maiores que este valor (0 = todos)."
    )

# Botão de busca
search_clicked = st.button("Buscar Links", type="primary", use_container_width=True)

if search_clicked:
    if not keyword.strip():
        st.error("Por favor, insira uma palavra-chave para realizar a busca.")
    elif not api_key or api_key == "SUA_CHAVE_API_AQUI":
        st.error("Por favor, configure a chave de API em `.streamlit/secrets.toml` antes de buscar.")
    else:
        with st.spinner("Consultando YouTube Data API v3 (/search, /videos, /channels)..."):
            search_endpoint = "https://www.googleapis.com/youtube/v3/search"
            search_params = {
                "part": "id,snippet",
                "q": keyword.strip(),
                "type": "video",
                "maxResults": 50,
                "order": "viewCount",
                "key": api_key
            }

            # Adiciona o regionCode se um país específico foi selecionado
            region_code = COUNTRY_OPTIONS.get(selected_country_label, "")
            if region_code:
                search_params["regionCode"] = region_code

            # Adiciona o relevanceLanguage se um idioma específico foi selecionado
            relevance_language = LANGUAGE_OPTIONS.get(selected_language_label, "")
            if relevance_language:
                search_params["relevanceLanguage"] = relevance_language

            try:
                # 1ª Requisição: Busca de vídeos ordenados por viewCount com filtros regionais/idiomáticos
                search_response = requests.get(search_endpoint, params=search_params, timeout=15)
                search_data = search_response.json()

                if search_response.status_code == 200:
                    search_items = search_data.get("items", [])
                    video_ids = [
                        item["id"]["videoId"]
                        for item in search_items
                        if item.get("id", {}).get("videoId")
                    ]

                    if video_ids:
                        # 2ª Requisição: Estatísticas e detalhes dos vídeos via endpoint /videos
                        videos_endpoint = "https://www.googleapis.com/youtube/v3/videos"
                        videos_params = {
                            "part": "snippet,statistics",
                            "id": ",".join(video_ids),
                            "key": api_key
                        }

                        videos_response = requests.get(videos_endpoint, params=videos_params, timeout=15)
                        videos_data = videos_response.json()

                        if videos_response.status_code == 200:
                            video_items = videos_data.get("items", [])

                            # Extração dos IDs únicos de canais
                            channel_ids = list({
                                item.get("snippet", {}).get("channelId")
                                for item in video_items
                                if item.get("snippet", {}).get("channelId")
                            })

                            # 3ª Requisição: Estatísticas dos canais via endpoint /channels (em lote)
                            channel_subs_map = {}
                            if channel_ids:
                                channels_endpoint = "https://www.googleapis.com/youtube/v3/channels"
                                channels_params = {
                                    "part": "statistics",
                                    "id": ",".join(channel_ids),
                                    "key": api_key
                                }

                                channels_response = requests.get(channels_endpoint, params=channels_params, timeout=15)
                                if channels_response.status_code == 200:
                                    channels_data = channels_response.json()
                                    for ch_item in channels_data.get("items", []):
                                        ch_id = ch_item.get("id")
                                        subs_raw = ch_item.get("statistics", {}).get("subscriberCount", "0")
                                        subs_count = int(subs_raw) if str(subs_raw).isdigit() else 0
                                        channel_subs_map[ch_id] = subs_count

                            # Filtragem em Python: viewCount >= min_views E subscriberCount >= min_subs
                            video_links = []
                            video_details = []

                            for item in video_items:
                                vid = item.get("id")
                                snippet = item.get("snippet", {})
                                statistics = item.get("statistics", {})
                                cid = snippet.get("channelId")

                                view_count_raw = statistics.get("viewCount", "0")
                                view_count = int(view_count_raw) if str(view_count_raw).isdigit() else 0

                                subscriber_count = channel_subs_map.get(cid, 0)

                                if view_count >= min_views and subscriber_count >= min_subs:
                                    url = f"https://www.youtube.com/watch?v={vid}"
                                    title = snippet.get("title", "Sem título")
                                    channel = snippet.get("channelTitle", "Canal desconhecido")

                                    video_links.append(url)
                                    video_details.append({
                                        "title": title,
                                        "channel": channel,
                                        "url": url,
                                        "views": view_count,
                                        "subscribers": subscriber_count
                                    })

                            if video_links:
                                links_text = "\n".join(video_links)
                                st.session_state.search_results = {
                                    "keyword": keyword.strip(),
                                    "country": selected_country_label,
                                    "language": selected_language_label,
                                    "min_views": min_views,
                                    "min_subs": min_subs,
                                    "video_links": video_links,
                                    "video_details": video_details,
                                    "links_text": links_text
                                }
                            else:
                                st.session_state.search_results = None
                                st.warning("Foram encontrados vídeos, mas nenhum atendeu aos critérios de filtros aplicados.")
                        else:
                            st.session_state.search_results = None
                            err_info = videos_data.get("error", {})
                            st.error(f"❌ Erro ao consultar detalhes dos vídeos: {err_info.get('message', 'Erro desconhecido')}")
                    else:
                        st.session_state.search_results = None
                        st.info("Nenhum vídeo encontrado para essa palavra-chave.")

                else:
                    st.session_state.search_results = None
                    error_info = search_data.get("error", {})
                    error_message = error_info.get("message", "Erro desconhecido ao consultar a API.")
                    error_code = error_info.get("code", search_response.status_code)
                    
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
    country_used = results.get("country", "Qualquer País")
    language_used = results.get("language", "Qualquer Idioma")
    min_views_used = results.get("min_views", 0)
    min_subs_used = results.get("min_subs", 0)
    video_links = results["video_links"]
    video_details = results["video_details"]
    links_text = results["links_text"]

    filter_tags = []
    if country_used != "Qualquer País":
        filter_tags.append(f"País: {country_used}")
    if language_used != "Qualquer Idioma":
        filter_tags.append(f"Idioma: {language_used}")
    if min_views_used > 0:
        filter_tags.append(f"≥ {min_views_used:,} views".replace(",", "."))
    if min_subs_used > 0:
        filter_tags.append(f"≥ {format_compact_number(min_subs_used)} inscritos")
    filter_msg = f" ({', '.join(filter_tags)})" if filter_tags else ""

    st.success(f"Foram encontrados **{len(video_links)}** vídeos para a busca: *'{keyword_used}'*{filter_msg}")
    
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
            st.session_state.country_input = "Qualquer País"
            st.session_state.language_input = "Qualquer Idioma"
            st.session_state.min_views_input = 0
            st.session_state.min_subs_input = 0
            st.rerun()

    # Exibição dos detalhes dos vídeos encontrados com views e inscritos formatados
    with st.expander("🔍 Ver detalhes dos vídeos encontrados"):
        for idx, detail in enumerate(video_details, 1):
            views_formatted = f"{detail['views']:,}".replace(",", ".")
            subs_formatted = format_compact_number(detail.get("subscribers", 0))
            st.markdown(
                f"**{idx}. [{detail['title']}]({detail['url']})** — 👁️ **{views_formatted}** views — 👤 *{detail['channel']}* (**{subs_formatted}** inscritos)"
            )
