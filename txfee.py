import streamlit as st
import pandas as pd
import sqlite3
import locale

# Tenta configurar o locale para o formato brasileiro (pt_BR).
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except locale.Error:
    locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil.1252')

# Conexão com o banco de dados SQLite
conn = sqlite3.connect('performance_data.db')
c = conn.cursor()

# Criação da tabela no banco de dados se ela não existir
def create_table():
    c.execute('''
    CREATE TABLE IF NOT EXISTS performance (
        mes TEXT, 
        valor_carteira REAL, 
        rentabilidade_carteira REAL, 
        rentabilidade_benchmark REAL, 
        taxa_performance REAL,
        high_watermark REAL
    )
    ''')
    conn.commit()

# Chamada da função para criar a tabela
create_table()

# Interface do Usuário
st.title("Calculadora de Taxa de Performance")

with st.form("my_form"):
    mes = st.text_input("Mês de Referência")
    valor_carteira = st.number_input("Valor da Carteira", step=0.01, format="%.2f")
    rentabilidade_carteira = st.number_input("Rentabilidade da Carteira (%)", step=0.01, format="%.2f")
    rentabilidade_benchmark = st.number_input("Rentabilidade do Benchmark (%)", step=0.01, format="%.2f")
    submitted = st.form_submit_button("Calcular Taxa de Performance")

    if submitted:
        # Cálculo do rendimento absoluto da carteira e do benchmark
        rendimento_carteira = valor_carteira * (rentabilidade_carteira / 100)
        rendimento_benchmark = valor_carteira * (rentabilidade_benchmark / 100)
        
        # Cálculo do rendimento que excede o benchmark
        rendimento_excedente = max(0, rendimento_carteira - rendimento_benchmark)
        
        # Cálculo da taxa de performance sobre o excedente
        taxa_performance = rendimento_excedente * 0.20

        # Verificação e atualização da linha d'água (high watermark)
        c.execute('SELECT MAX(high_watermark) FROM performance')
        last_high_watermark = c.fetchone()[0] or 0

        high_watermark = max(valor_carteira, last_high_watermark)

        # Inserção dos dados no banco de dados
        c.execute('''
        INSERT INTO performance (mes, valor_carteira, rentabilidade_carteira, rentabilidade_benchmark, taxa_performance, high_watermark) 
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (mes, valor_carteira, rentabilidade_carteira, rentabilidade_benchmark, taxa_performance, high_watermark))
        conn.commit()

        st.success("Dados inseridos com sucesso e taxa de performance calculada: R$ {:.2f}".format(taxa_performance))

# Exibição do histórico de dados
if st.button("Mostrar Histórico"):
    df = pd.read_sql_query("SELECT * FROM performance", conn)
    
    # Ajustando o formato dos números para o formato de moeda
    df['valor_carteira'] = df['valor_carteira'].apply(lambda x: f"R$ {x:,.2f}")
    df['taxa_performance'] = df['taxa_performance'].apply(lambda x: f"R$ {x:,.2f}")
    df['high_watermark'] = df['high_watermark'].apply(lambda x: f"R$ {x:,.2f}")
    
    st.dataframe(df)

# Fechamento da conexão com o banco de dados
conn.close()
