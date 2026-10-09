import streamlit as st
import streamlit.components.v1 as components
import requests
import json
import time
import re
from datetime import datetime

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

# Mapeamento de Idiomas para ISO 639-1
LANGUAGE_OPTIONS = {
    "Qualquer Idioma": "",
    "Alemão (de)": "de",
    "Inglês (en)": "en",
    "Português (pt)": "pt",
    "Espanhol (es)": "es",
    "Francês (fr)": "fr",
    "Italiano (it)": "it",
    "Holandês (nl)": "nl",
    "Japonês (ja)": "ja"
}

# Mapeamento de Ordenação
ORDER_OPTIONS = {
    "Mais Visualizados": "viewCount",
    "Relevância": "relevance",
    "Mais Recentes": "date"
}

# Inicialização do estado da sessão (st.session_state)
if "search_results" not in st.session_state:
    st.session_state.search_results = None

if "keyword_input" not in st.session_state:
    st.session_state.keyword_input = ""

if "language_input" not in st.session_state:
    st.session_state.language_input = "Qualquer Idioma"

if "order_input" not in st.session_state:
    st.session_state.order_input = "Mais Visualizados"

if "strict_title_input" not in st.session_state:
    st.session_state.strict_title_input = False

if "min_views_input" not in st.session_state:
    st.session_state.min_views_input = 0

if "min_subs_input" not in st.session_state:
    st.session_state.min_subs_input = 0

if "last_search_time" not in st.session_state:
    st.session_state.last_search_time = 0.0

# -------------------------------------------------------------
# Camada de Cache para Economia de Quota (1 hora de TTL)
# -------------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_youtube_data(keyword: str, api_key: str, language: str = "", order: str = "viewCount"):
    """
    Executa a busca no YouTube Data API com cache em memória
    para economizar a quota diária (102 unidades por busca).
    """
    search_endpoint = "https://www.googleapis.com/youtube/v3/search"
    search_params = {
        "part": "id,snippet",
        "q": keyword,
        "type": "video",
        "maxResults": 50,
        "order": order,
        "key": api_key
    }
    if language:
        search_params["relevanceLanguage"] = language
    
    headers = {
        "User-Agent": "Botlinks-Extractor/1.0"
    }

    # 1ª Requisição: /search (100 unidades)
    search_resp = requests.get(search_endpoint, params=search_params, headers=headers, timeout=15)
    if search_resp.status_code != 200:
        return {"error": search_resp.json().get("error", {}), "status": search_resp.status_code}
    
    search_data = search_resp.json()
    search_items = search_data.get("items", [])
    video_ids = [
        item["id"]["videoId"] for item in search_items 
        if item.get("id", {}).get("videoId")
    ]

    if not video_ids:
        return {"items": [], "channel_subs": {}}

    # 2ª Requisição: /videos (1 unidade)
    videos_endpoint = "https://www.googleapis.com/youtube/v3/videos"
    videos_params = {
        "part": "snippet,statistics",
        "id": ",".join(video_ids),
        "key": api_key
    }
    videos_resp = requests.get(videos_endpoint, params=videos_params, headers=headers, timeout=15)
    if videos_resp.status_code != 200:
        return {"error": videos_resp.json().get("error", {}), "status": videos_resp.status_code}
    
    video_items = videos_resp.json().get("items", [])

    # 3ª Requisição: /channels em lote (1 unidade)
    channel_ids = list({
        item.get("snippet", {}).get("channelId")
        for item in video_items
        if item.get("snippet", {}).get("channelId")
    })

    channel_subs_map = {}
    if channel_ids:
        channels_endpoint = "https://www.googleapis.com/youtube/v3/channels"
        channels_params = {
            "part": "statistics",
            "id": ",".join(channel_ids),
            "key": api_key
        }
        channels_resp = requests.get(channels_endpoint, params=channels_params, headers=headers, timeout=15)
        if channels_resp.status_code == 200:
            for ch in channels_resp.json().get("items", []):
                ch_id = ch.get("id")
                raw_subs = ch.get("statistics", {}).get("subscriberCount", "0")
                channel_subs_map[ch_id] = int(raw_subs) if str(raw_subs).isdigit() else 0

    return {"items": video_items, "channel_subs": channel_subs_map}

# -------------------------------------------------------------
# Utilitários de Formatação e Segurança
# -------------------------------------------------------------
def format_compact_number(num: int) -> str:
    if num >= 1_000_000:
        val = num / 1_000_000
        return f"{val:.1f}M".replace(".0M", "M")
    elif num >= 1_000:
        val = num / 1_000
        return f"{val:.1f}K".replace(".0K", "K")
    return str(num)

def sanitize_filename(name: str) -> str:
    """Sanitiza strings para uso seguro como nome de arquivo."""
    clean = re.sub(r'[^a-zA-Z0-9_\-]', '_', name.strip())
    return clean[:50] if clean else "links"

def render_copy_button(text_to_copy: str):
    """Renderiza o botão de cópia com sanitização contra quebra de tag script."""
    escaped_text = json.dumps(text_to_copy).replace("</", "<\\/")
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
            body {{ background: transparent; display: flex; align-items: center; height: 100%; overflow: hidden; }}
            .copy-btn {{
                width: 100%; height: 38px; display: inline-flex; align-items: center; justify-content: center;
                background-color: #262730; color: #FAFAFA; border: 1px solid rgba(250, 250, 250, 0.2);
                border-radius: 8px; font-size: 14px; font-weight: 500; cursor: pointer; transition: all 0.2s ease-in-out;
                outline: none; user-select: none;
            }}
            .copy-btn:hover {{ border-color: #FF0000; color: #FF0000; background-color: #1E1E24; }}
            .copy-btn.copied {{ background-color: #1E3A2F !important; border-color: #28a745 !important; color: #4cd964 !important; }}
        </style>
    </head>
    <body>
        <button id="btn-copy" class="copy-btn" onclick="copyContent()">📋 Copiar Todos</button>
        <script>
            const textToCopy = {escaped_text};
            function copyContent() {{
                if (navigator.clipboard && window.isSecureContext) {{
                    navigator.clipboard.writeText(textToCopy).then(() => setSuccess()).catch(() => fallbackCopy(textToCopy));
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
                try {{ document.execCommand('copy'); setSuccess(); }} catch (err) {{}}
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

# -------------------------------------------------------------
# Interface Principal
# -------------------------------------------------------------
st.markdown('<div class="main-title">🎥 Extrator de Links do YouTube</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Busque vídeos por palavra-chave, filtre por métricas e copie links em massa com segurança.</div>', unsafe_allow_html=True)

# Gestão de Chave de API (Secrets)
api_key = st.secrets.get("YOUTUBE_API_KEY", "")

if not api_key or api_key == "SUA_CHAVE_API_AQUI":
    st.warning(
        "⚠️ **Chave da API não configurada!**\n\n"
        "Configure sua chave no arquivo `.streamlit/secrets.toml`:\n"
        "```toml\n"
        'YOUTUBE_API_KEY = "sua_chave_real_aqui"\n'
        "```"
    )

# Validação e Limitação de Entrada do Utilizador
keyword = st.text_input(
    label="Palavra-chave ou termo de pesquisa:",
    placeholder="Ex: inteligência artificial, podcast de tecnologia, lofi hip hop...",
    max_chars=120,
    help="Digite o termo que deseja pesquisar no YouTube (máximo de 120 caracteres).",
    key="keyword_input"
)

# Linha 1 de Filtros: Idioma e Ordenação
col_lang, col_order = st.columns(2)

with col_lang:
    selected_language = st.selectbox(
        label="Idioma do Vídeo:",
        options=list(LANGUAGE_OPTIONS.keys()),
        key="language_input",
        help="Prioriza conteúdos no idioma selecionado via relevanceLanguage da API do YouTube."
    )

with col_order:
    selected_order = st.selectbox(
        label="Ordenar por:",
        options=list(ORDER_OPTIONS.keys()),
        key="order_input",
        help="Critério de ordenação da busca da API do YouTube."
    )

# Linha 2 de Filtros: Visualizações e Inscritos Mínimos
col_views, col_subs = st.columns(2)

with col_views:
    min_views = st.number_input(
        label="Visualizações mínimas:",
        min_value=0,
        max_value=1_000_000_000,
        value=0,
        step=1000,
        key="min_views_input",
        help="Filtra apenas vídeos com visualizações iguais ou maiores que este valor."
    )

with col_subs:
    min_subs = st.number_input(
        label="Inscritos mínimos:",
        min_value=0,
        max_value=1_000_000_000,
        value=0,
        step=1000,
        key="min_subs_input",
        help="Filtra apenas canais com inscritos iguais ou maiores que este valor."
    )

# Opção de Correspondência Estrita no Título
strict_title = st.checkbox(
    label="🎯 Exigir termo no título do vídeo",
    value=False,
    key="strict_title_input",
    help="Descarta vídeos cujo título não contenha as palavras pesquisadas (impede que vídeos com termos apenas na descrição, tags ou em outros idiomas sejam listados)."
)

search_clicked = st.button("Buscar Links", type="primary", use_container_width=True)

if search_clicked:
    current_time = time.time()
    # Rate limiting: 3 segundos de cooldown entre requisições na mesma sessão
    if current_time - st.session_state.last_search_time < 3.0:
        st.warning("⏱️ Por favor, aguarde alguns segundos antes de realizar uma nova busca.")
    elif not keyword.strip():
        st.error("Por favor, insira uma palavra-chave para realizar a busca.")
    elif not api_key or api_key == "SUA_CHAVE_API_AQUI":
        st.error("Por favor, configure a chave de API em `.streamlit/secrets.toml` antes de buscar.")
    else:
        st.session_state.last_search_time = current_time
        with st.spinner("Consultando YouTube Data API v3 (com cache ativado)..."):
            clean_keyword = " ".join(keyword.strip().split())
            lang_code = LANGUAGE_OPTIONS.get(selected_language, "")
            order_code = ORDER_OPTIONS.get(selected_order, "viewCount")

            result = fetch_youtube_data(clean_keyword, api_key, language=lang_code, order=order_code)

            if "error" in result:
                err = result["error"]
                err_code = result.get("status", 400)
                st.error(f"❌ **Erro na requisição ({err_code})**: {err.get('message', 'Falha na comunicação com a API.')}")
                if err_code == 403:
                    st.info("💡 **Dica**: Verifique se a YouTube Data API v3 está habilitada no Google Cloud ou se a cota diária de 10.000 unidades foi atingida.")
            else:
                video_items = result.get("items", [])
                channel_subs_map = result.get("channel_subs", {})

                video_links = []
                video_details = []

                # Preparação dos termos para verificação no título
                keywords_to_check = []
                exact_phrase_mode = False
                if strict_title:
                    if clean_keyword.startswith('"') and clean_keyword.endswith('"') and len(clean_keyword) > 2:
                        keywords_to_check = [clean_keyword[1:-1].strip().lower()]
                        exact_phrase_mode = True
                    else:
                        keywords_to_check = [w.lower() for w in clean_keyword.split() if w.strip()]

                for item in video_items:
                    vid = item.get("id")
                    snippet = item.get("snippet", {})
                    statistics = item.get("statistics", {})
                    cid = snippet.get("channelId")

                    title = snippet.get("title", "Sem título")
                    title_lower = title.lower()

                    # Validação de correspondência no título
                    if strict_title:
                        if exact_phrase_mode:
                            if keywords_to_check[0] not in title_lower:
                                continue
                        else:
                            if not all(w in title_lower for w in keywords_to_check):
                                continue

                    view_count_raw = statistics.get("viewCount", "0")
                    view_count = int(view_count_raw) if str(view_count_raw).isdigit() else 0
                    subscriber_count = channel_subs_map.get(cid, 0)

                    if view_count >= min_views and subscriber_count >= min_subs:
                        url = f"https://www.youtube.com/watch?v={vid}"
                        channel = snippet.get("channelTitle", "Canal desconhecido")

                        # Extração e formatação da data de publicação
                        published_raw = snippet.get("publishedAt", "")
                        published_date = "N/D"
                        if published_raw:
                            try:
                                dt = datetime.fromisoformat(published_raw.replace("Z", "+00:00"))
                                published_date = dt.strftime("%d/%m/%Y")
                            except Exception:
                                published_date = published_raw[:10]

                        video_links.append(url)
                        video_details.append({
                            "title": title,
                            "channel": channel,
                            "url": url,
                            "views": view_count,
                            "subscribers": subscriber_count,
                            "published_date": published_date
                        })

                if video_links:
                    links_text = "\n".join(video_links)
                    st.session_state.search_results = {
                        "keyword": clean_keyword,
                        "language": selected_language,
                        "order": selected_order,
                        "strict_title": strict_title,
                        "min_views": min_views,
                        "min_subs": min_subs,
                        "video_links": video_links,
                        "video_details": video_details,
                        "links_text": links_text
                    }
                else:
                    st.session_state.search_results = None
                    st.warning("Nenhum vídeo atendeu aos critérios de filtros estabelecidos.")

# -------------------------------------------------------------
# Exibição dos Resultados
# -------------------------------------------------------------
if st.session_state.search_results:
    results = st.session_state.search_results
    keyword_used = results["keyword"]
    language_used = results.get("language", "Qualquer Idioma")
    order_used = results.get("order", "Mais Visualizados")
    strict_title_used = results.get("strict_title", False)
    min_views_used = results.get("min_views", 0)
    min_subs_used = results.get("min_subs", 0)
    video_links = results["video_links"]
    video_details = results["video_details"]
    links_text = results["links_text"]

    filter_tags = []
    if language_used != "Qualquer Idioma":
        filter_tags.append(f"Idioma: {language_used}")
    if order_used != "Mais Visualizados":
        filter_tags.append(f"Ordem: {order_used}")
    if strict_title_used:
        filter_tags.append("Termo no título")
    if min_views_used > 0:
        filter_tags.append(f"≥ {min_views_used:,} views".replace(",", "."))
    if min_subs_used > 0:
        filter_tags.append(f"≥ {format_compact_number(min_subs_used)} inscritos")
    filter_msg = f" ({', '.join(filter_tags)})" if filter_tags else ""

    st.success(f"Foram encontrados **{len(video_links)}** vídeos para a busca: *'{keyword_used}'*{filter_msg}")
    
    st.subheader("📋 Links extraídos (prontos para cópia)")
    st.text_area(
        label="Links dos Vídeos (1 por linha):",
        value=links_text,
        height=280,
        help="Clique dentro da caixa, selecione tudo (Ctrl+A) e copie (Ctrl+C)."
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        render_copy_button(links_text)

    with col2:
        safe_filename = sanitize_filename(keyword_used)
        st.download_button(
            label="💾 Baixar (.txt)",
            data=links_text,
            file_name=f"youtube_links_{safe_filename}.txt",
            mime="text/plain",
            use_container_width=True
        )

    with col3:
        if st.button("🗑️ Limpar", use_container_width=True):
            st.session_state.search_results = None
            st.session_state.keyword_input = ""
            st.session_state.language_input = "Qualquer Idioma"
            st.session_state.order_input = "Mais Visualizados"
            st.session_state.strict_title_input = False
            st.session_state.min_views_input = 0
            st.session_state.min_subs_input = 0
            st.rerun()

    with st.expander("🔍 Ver detalhes dos vídeos encontrados"):
        for idx, detail in enumerate(video_details, 1):
            views_formatted = f"{detail['views']:,}".replace(",", ".")
            subs_formatted = format_compact_number(detail.get("subscribers", 0))
            published_formatted = detail.get("published_date", "N/D")
            # Sanitização de colchetes no Markdown para não quebrar hiperlinks
            safe_title = detail['title'].replace("[", "\\[").replace("]", "\\]")
            st.markdown(
                f"**{idx}. [{safe_title}]({detail['url']})** — 📅 {published_formatted} — 👁️ **{views_formatted}** views — 👤 *{detail['channel']}* (**{subs_formatted}** inscritos)"
            )
