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
Este aplicativo visa demonstrar o uso dos três algoritmos de pesquisa: 
* Pesquisa Sequencial, 
* Pesquisa Indexada,
* Pesquisa por HashMap
Avaliando o tempo de resposta de cada um deles.

Para realizar a demonstração, digite o **Nome Completo** ou o **CPF** na caixa de pesquisa e clique no botão **Buscar**.
*Nota 1: Para demonstrar a eficiência O(1) do HashMap, a busca deve ser exata.*

Visualize a tabela de dados na seção Área acadêmica caso não saiba o que pesquisar!
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

except Exception as e:
    st.error(f"Erro de conexão: {e}")
    st.stop()

st.divider() 

# --- INPUT DO USUÁRIO ---
# CSS Injetado para dar estilo de "Cartão" ao formulário (Fundo + Borda)
st.markdown("""
<style>
    [data-testid="stForm"] {
        background-color: var(--secondary-background-color);
        padding: 20px;
        border-radius: 10px;
        border: 1px solid rgba(250, 250, 250, 0.1);
    }
</style>
""", unsafe_allow_html=True)

# Usamos st.form para permitir que a tecla ENTER submeta a busca
with st.form(key='search_form'):
    col_search, col_btn = st.columns([3, 1], vertical_alignment="bottom") 
    with col_search:
        termo = st.text_input("Digite NOME COMPLETO ou CPF:", placeholder="Ex: Augusto Sampaio ou 760.142.958-01")
    with col_btn:
        # Em um formulário, o botão deve ser form_submit_button
        executar = st.form_submit_button("🔍 Buscar", type="primary", use_container_width=True)

# Exibe a mensagem de status do sistema logo abaixo do botão/formulário
if 'hash_db' in locals():
    st.success(f"✅ Sistema Online. {len(hash_db)} chaves de busca em memória (Indexando Nomes + CPFs).")

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

# 1. TABELA DE DADOS (PRIMEIRO)
if st.toggle("📂 Ver Tabela de Dados (Amostra)"):
    with st.spinner("Buscando dados no banco..."):
        conn = get_connection()
        df_dados = pd.read_sql("SELECT * FROM dados", conn)
        st.info(f"Exibindo todos os {len(df_dados)} registros da base.")
        st.dataframe(df_dados, hide_index=True)
        conn.close()

st.write("") 

# 2. RELATÓRIO TÉCNICO (SEGUNDO)
if st.toggle("📄 Ver Relatório Técnico"):
    st.markdown("""
    ### Relatório Técnico: Desenvolvimento de Benchmark de Algoritmos de Busca
    **Aluno:** Wesley Dias Fróes  
    **Disciplina:** Algoritmos e Estrutura de Dados II  
    **Professora:** Dana Tomazett

    #### 1. Introdução
    Este projeto tem como objetivo demonstrar, na prática, a aplicação da teoria de complexidade de algoritmos (Notação Big O - ferramenta matemática usada para descrever o desempenho de um algoritmo, especialmente como sua complexidade de tempo ou espaço escala conforme o tamanho da entrada cresce.). Foi desenvolvida uma aplicação Web capaz de comparar o desempenho de três métodos de busca de dados (Sequencial, Indexada e HashMap) em um ambiente de banco de dados real hospedado na nuvem.

    #### 2. Etapa 1: Modelagem e Preparação dos Dados (Local)
    O projeto iniciou-se com a estruturação da massa de dados necessária para os testes.
    * **Origem:** Os dados brutos foram organizados inicialmente em planilhas Excel e convertidos para o formato `.csv`.
    * **Modelagem Local:** Utilizando o **MySQL Workbench**, foi criado um banco de dados local. A importação dos dados `.csv` permitiu povoar a tabela `dados` com mais de 5.000 registros, contendo informações como Nome, CPF, Endereço e Telefone. Esta etapa garantiu a integridade e a tipagem correta das colunas antes da migração para a nuvem.

    #### 3. Etapa 2: Migração para a Nuvem (Cloud Database)
    Para que a aplicação fosse acessível via internet, o banco de dados não poderia residir apenas no computador local (`localhost`).
    * **Provedor Escolhido:** Utilizou-se a plataforma **Aiven**, um serviço de DBaaS (Database as a Service), para hospedar uma instância MySQL gerenciada.
    * **Migração:** Através do MySQL Workbench, foi realizada uma conexão remota com o servidor da Aiven. O *dump* (backup) do banco local foi executado no servidor remoto, replicando a estrutura da tabela e os dados na nuvem.
    * **Indexação:** Nesta fase, foi essencial garantir a criação de índices (B-Tree) nas colunas de busca para diferenciar a performance da busca indexada em relação à busca sequencial.

    #### 4. Etapa 3: Desenvolvimento da Lógica (Python + Streamlit)
    O "cérebro" da aplicação foi desenvolvido em Python, utilizando a biblioteca **Streamlit** para criar o Frontend e o Backend simultaneamente.
    * **Conexão:** Implementou-se o conector `mysql-connector-python` para estabelecer a comunicação segura entre a aplicação e o banco Aiven.
    * **Implementação dos Algoritmos:**
        1. **Busca Sequencial:** Simulada através de queries SQL que percorrem a tabela linearmente (Full Table Scan).
        2. **Busca Indexada:** Utiliza os recursos nativos de indexação do MySQL para localização rápida.
        3. **HashMap:** Implementada carregando os dados (ID, Nome e CPF) para a memória RAM do servidor (Dicionário Python) na inicialização do sistema, permitindo acesso instantâneo.
    * **Funcionalidades Extras:** Foram adicionados gráficos comparativos, exibição dos dados retornados e uma "Área Acadêmica" que permite ao avaliador inspecionar o código-fonte e a tabela de dados em tempo real.

    #### 5. Etapa 4: Versionamento e Preparação para Deploy
    Para publicar o projeto, utilizou-se o **GitHub** como repositório de código.
    * **Estrutura do Repositório:** O código foi organizado contendo:
        * `app.py`: O código-fonte principal.
        * `requirements.txt`: Arquivo crucial contendo a lista de dependências (`streamlit`, `pandas`, `mysql-connector-python`) para que o servidor saiba o que instalar.
        * `image_7.png`: Recursos visuais (logomarca).
    * **Correções Técnicas:** Durante esta fase, ajustou-se a nomenclatura do arquivo principal para `app.py` (em minúsculo), atendendo aos requisitos de sistemas baseados em Linux, que diferenciam maiúsculas de minúsculas.

    #### 6. Etapa 5: Publicação Online (Streamlit Cloud)
    A etapa final consistiu em colocar a aplicação no ar.
    * **Integração CI/CD:** O **Streamlit Community Cloud** foi conectado ao repositório do GitHub.
    * **Deploy:** Ao configurar o deploy, o servidor do Streamlit leu o arquivo `requirements.txt`, instalou as bibliotecas necessárias e executou o `app.py`.
    * **Resultado:** A aplicação está agora 100% online, responsiva (adaptável a celulares e computadores) e conectada em tempo real ao banco de dados, permitindo a demonstração da performance dos algoritmos de qualquer lugar.

    #### 7. Conclusão
    Este projeto integrou com sucesso os conceitos teóricos de Estrutura de Dados com práticas modernas de Engenharia de Software e Cloud Computing. O resultado final evidencia claramente a superioridade do HashMap em velocidade, seguido pela Busca Indexada, provando a importância da escolha correta das estruturas de dados no desenvolvimento de sistemas.
    """)

st.write("") 

# 3. CÓDIGO FONTE (ÚLTIMO)
if st.toggle("💻 Ver Código Fonte Python"):
    with open(__file__, "r", encoding='utf-8') as f:
        codigo = f.read()
    st.code(codigo, language="python")

