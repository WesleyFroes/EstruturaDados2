import streamlit as st
import mysql.connector
import time
import pandas as pd
import os

# Configuração da página
st.set_page_config(page_title="Benchmark MySQL", page_icon="🏎️", layout="wide")

# --- CABEÇALHO INSTITUCIONAL ---
col_logo, col_header_text = st.columns([1.5, 5], vertical_alignment="center")

with col_logo:
    try:
        st.image("image_7.png", use_container_width=True) 
    except FileNotFoundError:
        st.warning("Imagem 'image_7.png' não encontrada.")

with col_header_text:
    st.markdown("""
    ## ALGORITMOS E ESTRUTURA DE DADOS II
    **Professora:** Dana Tomazett\n
    **Aluno:** Wesley Dias Fróes - **Matrícula:** 20232243038
    """, unsafe_allow_html=True)

st.divider() 

# --- TEXTO INTRODUTÓRIO ---
st.markdown("""
Este aplicativo visa demonstrar o uso dos três algoritmos de pesquisa estudados neste semestre em nosso curso de Algoritmos e Estrutura de Dados II e avaliar o tempo de resposta de cada um deles.
* Pesquisa Sequencial, 
* Pesquisa Indexada,
* Pesquisa por HashMap

Para realizar a demonstração, digite o **Nome Completo** ou o **CPF** na caixa de pesquisa e clique no botão **Buscar**.

*Nota 1: Para demonstrar a eficiência O(1) do HashMap, a busca deve ser exata.*
""")

# --- CONEXÃO COM O BANCO AIVEN ---
def get_connection():
    return mysql.connector.connect(
        host="mysql-3455cc47-wesleyfroes-5e7b.k.aivencloud.com",
        user="avnadmin",
        password="AVNS__rOT2E8RQkt_4-TPrSg", 
        database="dana", 
        port=27950
    )

# --- CARREGAR DADOS PARA MEMÓRIA ---
@st.cache_resource
def load_hashmap():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT ID, Nome, CPF FROM dados")
    result = cursor.fetchall()
    conn.close()
    
    hash_map = {}
    for row in result:
        if row[1]: hash_map[row[1]] = row[0]
        if row[2]: hash_map[row[2]] = row[0]
            
    return hash_map

try:
    with st.spinner('Carregando dados para memória RAM...'):
        hash_db = load_hashmap()
    st.success(f"✅ Sistema Online. {len(hash_db)} chaves de busca em memória (Indexando Nomes + CPFs).")
except Exception as e:
    st.error(f"Erro de conexão: {e}")
    st.stop()

# --- INPUT DO USUÁRIO ---
col_search, col_btn = st.columns([3, 1], vertical_alignment="bottom") 
with col_search:
    termo = st.text_input("Digite NOME COMPLETO ou CPF:", placeholder="Ex: Augusto Sampaio ou 760.142.958-01")
with col_btn:
    executar = st.button("🔍 Buscar", type="primary", use_container_width=True)

if executar:
    if not termo:
        st.warning("Digite algo para buscar.")
    else:
        tempos = {}
        dados_encontrados = None
        colunas_retornadas = []
        
        # 1. BUSCA SEQUENCIAL (O(n))
        conn = get_connection()
        cursor = conn.cursor()
        start = time.perf_counter()
        
        sql_sequencial = f"SELECT * FROM dados WHERE Nome = '{termo}' OR CPF = '{termo}'"
        cursor.execute(sql_sequencial)
        _ = cursor.fetchall()
        tempos['Sequencial'] = time.perf_counter() - start
        conn.close()

        # 2. BUSCA INDEXADA (O(log n))
        conn = get_connection()
        cursor = conn.cursor()
        start = time.perf_counter()
        
        sql_indexada = f"SELECT * FROM dados WHERE Nome = '{termo}' OR CPF = '{termo}'"
        cursor.execute(sql_indexada)
        dados_encontrados = cursor.fetchall()
        if cursor.description:
            colunas_retornadas = [i[0] for i in cursor.description]
            
        tempos['Indexada'] = time.perf_counter() - start
        conn.close()

        # 3. HASHMAP (O(1))
        start = time.perf_counter()
        _ = hash_db.get(termo)
        tempos['HashMap'] = time.perf_counter() - start

        # --- EXIBIÇÃO ---
        if dados_encontrados:
            st.success(f"✅ Registro Localizado! ({len(dados_encontrados)} ocorrências)")
            df_resultado = pd.DataFrame(dados_encontrados, columns=colunas_retornadas)
            st.dataframe(df_resultado, hide_index=True, use_container_width=True)
            
            st.divider()
            st.write("### ⏱️ Tempos de Execução")
            
            # Métricas
            c1, c2, c3 = st.columns(3)
            c1.metric("1. Sequencial", f"{tempos['Sequencial']:.5f}s")
            c2.metric("2. Indexada", f"{tempos['Indexada']:.5f}s")
            c3.metric("3. HashMap", f"{tempos['HashMap']:.8f}s")
            
            # Gráfico
            df_chart = pd.DataFrame([
                {"Método": "1. Sequencial", "Tempo (s)": tempos['Sequencial']},
                {"Método": "2. Indexada", "Tempo (s)": tempos['Indexada']},
                {"Método": "3. HashMap", "Tempo (s)": tempos['HashMap']}
            ])
            st.bar_chart(df_chart, x="Método", y="Tempo (s)", color="#00a8ff")

            # --- RANKING DE PERFORMANCE ---
            # Ordena do mais rápido (menor tempo) para o mais lento
            ranking = sorted(tempos.items(), key=lambda item: item[1])
            
            st.info(f"""
            **🏆 Ranking de Performance (Do mais rápido para o mais lento):**
            
            1. 🥇 **{ranking[0][0]}** - {ranking[0][1]:.6f}s
            2. 🥈 **{ranking[1][0]}** - {ranking[1][1]:.6f}s
            3. 🥉 **{ranking[2][0]}** - {ranking[2][1]:.6f}s
            """)

        else:
            st.error(f"❌ '{termo}' não encontrado. Lembre-se de digitar o Nome Completo ou CPF exato.")

# --- ÁREA ACADÊMICA ---
st.divider()
st.subheader("🎓 Área Acadêmica")
st.write("Recursos para validação do projeto.")

if st.toggle("💻 Ver Código Fonte Python"):
    with open(__file__, "r", encoding='utf-8') as f:
        codigo = f.read()
    st.code(codigo, language="python")

st.write("") 

if st.toggle("📂 Ver Tabela de Dados (Amostra)"):
    with st.spinner("Buscando dados no banco..."):
        conn = get_connection()
        df_dados = pd.read_sql("SELECT * FROM dados", conn)
        st.info(f"Exibindo todos os {len(df_dados)} registros da base.")
        st.dataframe(df_dados, hide_index=True)
        conn.close()