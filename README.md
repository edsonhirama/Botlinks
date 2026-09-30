# 🎥 Botlinks - Extrator de Links do YouTube

Aplicação web desenvolvida em **Streamlit** para buscar e extrair links de vídeos do YouTube em massa a partir de palavras-chave, utilizando a **YouTube Data API v3**.

---

## ✨ Funcionalidades

- 🔍 **Busca Otimizada**: Retorna até 50 vídeos mais relevantes por palavra-chave.
- 📋 **Cópia em Massa**: Botão com HTML/JavaScript para copiar todos os links com 1 clique diretamente para o clipboard.
- 💾 **Download em .txt**: Baixe a lista de links gerada instantaneamente.
- 🗑️ **Limpeza de Estado**: Botão para resetar a busca e limpar a tela com `st.session_state`.
- 🎨 **Tema Escuro Moderno**: Interface personalizada com botões e acentos em vermelho YouTube (`#FF0000`).
- 🔐 **Segurança com `st.secrets`**: Chave de API protegida e nunca exposta publicamente.

---

## 🚀 Como Executar Localmente

### 1. Clonar o repositório
```bash
git clone https://github.com/edsonhirama/Botlinks.git
cd Botlinks
```

### 2. Instalar dependências
```bash
pip install -r requirements.txt
```

### 3. Configurar a Chave da YouTube API
Crie o arquivo `.streamlit/secrets.toml` com a sua chave da YouTube Data API v3:
```toml
YOUTUBE_API_KEY = "SUA_CHAVE_API_AQUI"
```

### 4. Executar a aplicação
```bash
streamlit run app.py
```

---

## ☁️ Deploy no Streamlit Community Cloud

1. Acesse [share.streamlit.io](https://share.streamlit.io/) e conecte com sua conta GitHub.
2. Clique em **"New app"**.
3. Selecione o repositório `edsonhirama/Botlinks` e a branch `main` com arquivo principal `app.py`.
4. Em **Advanced settings... > Secrets**, adicione sua chave de API:
   ```toml
   YOUTUBE_API_KEY = "sua_chave_real_aqui"
   ```
5. Clique em **"Deploy!"**.
