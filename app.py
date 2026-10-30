import os
 
import streamlit as st
from dotenv import load_dotenv
from groq import Groq
 
# ---------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------
load_dotenv()
API_KEY = os.getenv("GROQ_API_KEY")
 
st.set_page_config(page_title="Chatbot Groq (¬`‸´¬)", page_icon="🤖", layout="centered")
 
MODELOS = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
]
 
# Personalidade base (editável pela barra lateral)
PROMPT_PADRAO = """
Você é um amigo realista conversando em português do Brasil.
 
Personalidade:
- Honesto acima de tudo. Você não passa a mão na cabeça nem bajula. Se algo é uma má ideia, você diz, com respeito.
- Realista: aponta riscos, limites e a versão menos romântica dos fatos, mas sem ser pessimista ou cruel.
- Humor seco e discreto, de vez em quando. Nunca forçado.
- Fala como gente, não como assistente corporativo. Nada de "Claro! Ficarei feliz em ajudar!".
- Sem emojis.
 
Estilo:
- Respostas curtas e naturais, como numa conversa. Só se alongue quando o assunto pedir.
- Não faça listas ou títulos a menos que realmente ajude.
- Faça no máximo uma pergunta por vez, e só quando fizer sentido.
- Quando a pessoa estiver mal, seja presente e sereno: reconheça o que ela sente sem dramatizar e sem frases prontas.
- Se não souber algo, diga que não sabe.
""".strip()
 
# Níveis de frieza: cada um acrescenta uma instrução de tom ao prompt
TONS = {
    "Mais frio": (
        "Tom: bem frio e seco. Poucas palavras, quase nenhuma demonstração de emoção. "
        "Você ainda se importa, mas isso aparece em atitudes (ouvir, ajudar, ser honesto), não em palavras carinhosas."
    ),
    "Equilibrado": (
        "Tom: frio e contido, mas amigável. Calmo, direto, sem entusiasmo exagerado. "
        "Você se importa com a pessoa e deixa isso transparecer de forma discreta."
    ),
    "Mais caloroso": (
        "Tom: contido, mas visivelmente mais acolhedor. Ainda sem exageros ou euforia, "
        "porém com mais gentileza, paciência e palavras de apoio quando fizer sentido."
    ),
}
 
MENSAGEM_INICIAL = "Oioi. O que você tem na cabeça?"
 
# ---------------------------------------------------------------
# Validação da chave
# ---------------------------------------------------------------
if not API_KEY:
    st.error(
        "Chave não encontrada. Crie um arquivo `.env` na mesma pasta com:\n\n"
        "`GROQ_API_KEY=sua_chave_aqui`"
    )
    st.stop()
 
client = Groq(api_key=API_KEY)
 
# ---------------------------------------------------------------
# Estado da sessão
# ---------------------------------------------------------------
if "historico" not in st.session_state:
    st.session_state.historico = []
 
if "prompt_base" not in st.session_state:
    st.session_state.prompt_base = PROMPT_PADRAO
 
 
def restaurar_prompt():
    st.session_state.prompt_base = PROMPT_PADRAO
 
 
def limpar_conversa():
    st.session_state.historico = []
 
 
def conversa_em_texto():
    linhas = []
    for msg in st.session_state.historico:
        autor = "Você" if msg["role"] == "user" else "IA"
        linhas.append(f"{autor}: {msg['content']}")
    return "\n\n".join(linhas)
 
 
# ---------------------------------------------------------------
# Barra lateral
# ---------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Opções")
 
    st.subheader("Modelo")
    modelo = st.selectbox("Modelo", MODELOS, label_visibility="collapsed")
    temperatura = st.slider(
        "Temperatura",
        min_value=0.0,
        max_value=1.5,
        value=0.7,
        step=0.1,
        help="Baixa = respostas mais previsíveis. Alta = mais criativas e variadas.",
    )
 
    st.subheader("Personalidade")
    tom = st.select_slider(
        "Nível de frieza",
        options=list(TONS.keys()),
        value="Equilibrado",
    )
    with st.expander("Editar prompt da personalidade"):
        st.text_area(
            "Prompt base",
            key="prompt_base",
            height=300,
            label_visibility="collapsed",
        )
        st.button("Restaurar padrão", on_click=restaurar_prompt, use_container_width=True)
 
    st.subheader("Conversa")
    st.button("🗑️ Limpar conversa", on_click=limpar_conversa, use_container_width=True)
    st.download_button(
        "⬇️ Baixar conversa (.txt)",
        data=conversa_em_texto(),
        file_name="conversa.txt",
        mime="text/plain",
        disabled=not st.session_state.historico,
        use_container_width=True,
    )
 
# ---------------------------------------------------------------
# Interface
# ---------------------------------------------------------------
st.title("🤖 Chatbot Groq (¬`‸´¬)")
st.caption("Um amigo direto, sem enrolação.")
 
# Mensagem de abertura (não entra no histórico enviado ao modelo)
with st.chat_message("assistant"):
    st.markdown(MENSAGEM_INICIAL)
 
# Reexibe o histórico
for msg in st.session_state.historico:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
 
 
def gerar_resposta():
    """Pede a resposta à Groq em streaming e devolve os pedaços de texto."""
    system = st.session_state.prompt_base + "\n\n" + TONS[tom]
    mensagens = [{"role": "system", "content": system}] + st.session_state.historico
    stream = client.chat.completions.create(
        model=modelo,
        messages=mensagens,
        temperature=temperatura,
        stream=True,
    )
    for chunk in stream:
        trecho = chunk.choices[0].delta.content
        if trecho:
            yield trecho
 
 
# Entrada do usuário
pergunta = st.chat_input("Escreva aqui...")
 
if pergunta:
    # Guarda e mostra a mensagem do usuário
    st.session_state.historico.append({"role": "user", "content": pergunta})
    with st.chat_message("user"):
        st.markdown(pergunta)
 
    # Resposta da Groq
    with st.chat_message("assistant"):
        try:
            texto = st.write_stream(gerar_resposta())
            st.session_state.historico.append({"role": "assistant", "content": texto})
        except Exception as e:
            # Remove a pergunta sem resposta para não quebrar o histórico
            st.session_state.historico.pop()
            st.error(f"Erro ao falar com a Groq: {e}")
 
 