import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import sqlite3
from datetime import datetime
import plotly.express as px

st.set_page_config(
    page_title="Projetos DF - ObrasGov.br",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Cache para carregar dados
@st.cache_data
def load_data():
    """Carrega dados do banco SQLite"""
    try:
        conn = sqlite3.connect('data/projetosDF.db')
        df = pd.read_sql_query("SELECT * FROM projetos", conn)
        conn.close()
        
        # Converter colunas de data
        date_cols = ['dataInicialPrevista', 'dataFinalPrevista', 'dataInicialEfetiva', 
                     'dataFinalEfetiva', 'dataCadastro', 'dataSituacao']
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Converter colunas numéricas
        df['quantidadeEmpregosGerados'] = pd.to_numeric(df['quantidadeEmpregosGerados'], errors='coerce')
        df['populacaoBeneficiada'] = pd.to_numeric(df['populacaoBeneficiada'], errors='coerce')
        
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

# Carregar dados
df = load_data()

# Sidebar - Filtros
st.sidebar.title("Filtros")

# Filtro por situação
situacoes = ['Todos'] + sorted(df['situacao'].dropna().unique().tolist())
situacao_selecionada = st.sidebar.selectbox("Situação do Projeto", situacoes)

# Filtro por espécie
especies = ['Todos'] + sorted(df['especie'].dropna().unique().tolist())
especie_selecionada = st.sidebar.selectbox("Espécie", especies)

# Filtro por natureza
naturezas = ['Todos'] + sorted(df['natureza'].dropna().unique().tolist())
natureza_selecionada = st.sidebar.selectbox("Natureza", naturezas)

# Filtro de data de cadastro
st.sidebar.subheader("Período de Cadastro")
df_com_data = df[df['dataCadastro'].notna()].copy()
if len(df_com_data) > 0:
    min_date = df_com_data['dataCadastro'].min().date()
    max_date = df_com_data['dataCadastro'].max().date()
    
    data_inicio = st.sidebar.date_input("Data Inicial", min_date, min_value=min_date, max_value=max_date)
    data_fim = st.sidebar.date_input("Data Final", max_date, min_value=min_date, max_value=max_date)
else:
    data_inicio = None
    data_fim = None

# Filtro por empregos/população
st.sidebar.subheader("Impacto Social")
tem_emprego = st.sidebar.checkbox("Apenas com dados de empregos", False)
tem_populacao = st.sidebar.checkbox("Apenas com dados de população", False)

# Busca por nome
st.sidebar.subheader("Busca")
busca_nome = st.sidebar.text_input("Buscar por nome do projeto")

# Aplicar filtros
df_filtrado = df.copy()

if situacao_selecionada != 'Todos':
    df_filtrado = df_filtrado[df_filtrado['situacao'] == situacao_selecionada]

if especie_selecionada != 'Todos':
    df_filtrado = df_filtrado[df_filtrado['especie'] == especie_selecionada]

if natureza_selecionada != 'Todos':
    df_filtrado = df_filtrado[df_filtrado['natureza'] == natureza_selecionada]

if data_inicio and data_fim:
    df_filtrado = df_filtrado[
        (df_filtrado['dataCadastro'].dt.date >= data_inicio) & 
        (df_filtrado['dataCadastro'].dt.date <= data_fim)
    ]

if tem_emprego:
    df_filtrado = df_filtrado[df_filtrado['quantidadeEmpregosGerados'] > 0]

if tem_populacao:
    df_filtrado = df_filtrado[df_filtrado['populacaoBeneficiada'] > 0]

if busca_nome:
    df_filtrado = df_filtrado[df_filtrado['nome'].str.contains(busca_nome, case=False, na=False)]

# Header principal
st.markdown('<p class="main-header">Análise de Projetos de Investimento - Distrito Federal</p>', unsafe_allow_html=True)
st.markdown("---")

# Métricas principais
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total de Projetos", f"{len(df_filtrado):,}".replace(',', '.'))

with col2:
    total_empregos = df_filtrado['quantidadeEmpregosGerados'].sum()
    st.metric("Empregos Gerados", f"{total_empregos:,.0f}".replace(',', '.'))

with col3:
    total_populacao = df_filtrado['populacaoBeneficiada'].sum()
    st.metric("População Beneficiada", f"{total_populacao:,.0f}".replace(',', '.'))

with col4:
    projetos_execucao = len(df_filtrado[df_filtrado['situacao'].str.contains('execução', case=False, na=False)])
    st.metric("Em Execução", projetos_execucao)

st.markdown("---")

# Tabs principais
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Visão Geral", 
    "Impacto Social", 
    "Análise Temporal",
    "Detalhamento",
    "Dados Brutos"
])

# TAB 1: Visão Geral
with tab1:
    st.header("Visão Geral dos Projetos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de situação
        st.subheader("Distribuição por Situação")
        if len(df_filtrado) > 0:
            situacao_counts = df_filtrado['situacao'].value_counts().reset_index()
            situacao_counts.columns = ['Situação', 'Quantidade']
            
            fig = px.bar(
                situacao_counts,
                x='Quantidade',
                y='Situação',
                orientation='h',
                color='Quantidade',
                color_continuous_scale='Blues'
            )
            fig.update_layout(showlegend=False, height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Nenhum dado disponível para exibir.")
    
    with col2:
        # Gráfico de espécie
        st.subheader("Top 10 Espécies")
        if len(df_filtrado) > 0:
            especie_counts = df_filtrado['especie'].value_counts().head(10)
            
            fig = px.pie(
                values=especie_counts.values,
                names=especie_counts.index,
                hole=0.4
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Nenhum dado disponível para exibir.")
    
    # Gráfico de natureza
    st.subheader("Distribuição por Natureza")
    natureza_counts = df_filtrado['natureza'].value_counts().head(10).reset_index()
    natureza_counts.columns = ['Natureza', 'Quantidade']
    
    fig = px.bar(
        natureza_counts,
        x='Natureza',
        y='Quantidade',
        color='Quantidade',
        color_continuous_scale='Viridis'
    )
    fig.update_layout(showlegend=False, height=400)
    st.plotly_chart(fig, use_container_width=True)

# TAB 2: Impacto Social
with tab2:
    st.header("Análise de Impacto Social")
    
    # Filtrar projetos com dados completos
    df_impacto = df_filtrado[
        (df_filtrado['quantidadeEmpregosGerados'] > 0) & 
        (df_filtrado['populacaoBeneficiada'] > 0)
    ].copy()
    
    if len(df_impacto) > 0:
        # Calcular taxa
        df_impacto['taxa_emprego_por_100'] = (
            df_impacto['quantidadeEmpregosGerados'] / 
            df_impacto['populacaoBeneficiada'] * 100
        )
        
        # Métricas de impacto
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Projetos com Dados Completos",
                f"{len(df_impacto)}",
                f"{len(df_impacto)/len(df_filtrado)*100:.1f}% do total"
            )
        
        with col2:
            taxa_media = df_impacto['taxa_emprego_por_100'].mean()
            st.metric(
                "Taxa Média Emprego/População",
                f"{taxa_media:.2f}%",
                "empregos por 100 pessoas"
            )
        
        with col3:
            taxa_mediana = df_impacto['taxa_emprego_por_100'].median()
            st.metric(
                "Taxa Mediana",
                f"{taxa_mediana:.2f}%",
                "empregos por 100 pessoas"
            )
        
        st.markdown("---")
        
        # Scatter plot interativo
        st.subheader("Relação: População Beneficiada vs Empregos Gerados")
        
        fig = px.scatter(
            df_impacto,
            x='populacaoBeneficiada',
            y='quantidadeEmpregosGerados',
            color='taxa_emprego_por_100',
            size='quantidadeEmpregosGerados',
            hover_data=['nome', 'situacao'],
            labels={
                'populacaoBeneficiada': 'População Beneficiada',
                'quantidadeEmpregosGerados': 'Empregos Gerados',
                'taxa_emprego_por_100': 'Taxa (%)'
            },
            color_continuous_scale='Viridis'
        )
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Top 10 por empregos
            st.subheader("Top 10 por Empregos Gerados")
            top_empregos = df_impacto.nlargest(10, 'quantidadeEmpregosGerados')[
                ['nome', 'quantidadeEmpregosGerados', 'populacaoBeneficiada', 'situacao']
            ].reset_index(drop=True)
            top_empregos.index = top_empregos.index + 1
            st.dataframe(top_empregos, width='stretch')
        
        with col2:
            # Top 10 por população
            st.subheader("Top 10 por População Beneficiada")
            top_populacao = df_impacto.nlargest(10, 'populacaoBeneficiada')[
                ['nome', 'populacaoBeneficiada', 'quantidadeEmpregosGerados', 'situacao']
            ].reset_index(drop=True)
            top_populacao.index = top_populacao.index + 1
            st.dataframe(top_populacao, width='stretch')
        
        # Top 10 mais eficientes
        st.subheader("Top 10 Projetos Mais Eficientes (Taxa Emprego/População)")
        top_eficiencia = df_impacto.nlargest(10, 'taxa_emprego_por_100')[
            ['nome', 'quantidadeEmpregosGerados', 'populacaoBeneficiada', 
             'taxa_emprego_por_100', 'situacao']
        ].reset_index(drop=True)
        top_eficiencia.index = top_eficiencia.index + 1
        top_eficiencia['taxa_emprego_por_100'] = top_eficiencia['taxa_emprego_por_100'].round(2)
        st.dataframe(top_eficiencia, width='stretch')
        
    else:
        st.warning("Nenhum projeto com dados completos de impacto social nos filtros selecionados.")

# TAB 3: Análise Temporal
with tab3:
    st.header("Análise Temporal")
    
    df_temporal = df_filtrado[df_filtrado['dataCadastro'].notna()].copy()
    
    if len(df_temporal) > 0:
        df_temporal['ano'] = df_temporal['dataCadastro'].dt.year
        df_temporal['mes_ano'] = df_temporal['dataCadastro'].dt.to_period('M').astype(str)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Projetos por ano
            st.subheader("Projetos Cadastrados por Ano")
            cadastros_ano = df_temporal.groupby('ano').size().reset_index(name='quantidade')
            
            fig = px.line(
                cadastros_ano,
                x='ano',
                y='quantidade',
                markers=True,
                labels={'ano': 'Ano', 'quantidade': 'Projetos Cadastrados'}
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Projetos por mês (últimos 24 meses)
            st.subheader("Projetos por Mês (Últimos 24)")
            cadastros_mes = df_temporal.groupby('mes_ano').size().tail(24).reset_index(name='quantidade')
            
            fig = px.bar(
                cadastros_mes,
                x='mes_ano',
                y='quantidade',
                labels={'mes_ano': 'Mês/Ano', 'quantidade': 'Projetos'},
                color='quantidade',
                color_continuous_scale='Blues'
            )
            fig.update_layout(height=400, showlegend=False)
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
        
        # Evolução por situação ao longo do tempo
        st.subheader("Evolução por Situação ao Longo do Tempo")
        evolucao = df_temporal.groupby(['ano', 'situacao']).size().reset_index(name='quantidade')
        
        fig = px.line(
            evolucao,
            x='ano',
            y='quantidade',
            color='situacao',
            markers=True,
            labels={'ano': 'Ano', 'quantidade': 'Quantidade de Projetos', 'situacao': 'Situação'}
        )
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.warning("Nenhum projeto com data de cadastro nos filtros selecionados.")

# TAB 4: Detalhamento
with tab4:
    st.header("Detalhamento dos Projetos")
    
    # Seletor de projeto
    projetos_lista = df_filtrado['nome'].unique().tolist()
    projeto_selecionado = st.selectbox("Selecione um projeto para ver detalhes", projetos_lista)
    
    if projeto_selecionado:
        projeto = df_filtrado[df_filtrado['nome'] == projeto_selecionado].iloc[0]
        
        st.subheader(f"{projeto['nome']}")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Informações Básicas**")
            st.write(f"**Situação:** {projeto['situacao']}")
            st.write(f"**Espécie:** {projeto['especie']}")
            st.write(f"**Natureza:** {projeto['natureza']}")
            st.write(f"**UF:** {projeto['uf']}")
        
        with col2:
            st.markdown("**Impacto Social**")
            empregos = projeto['quantidadeEmpregosGerados']
            populacao = projeto['populacaoBeneficiada']
            st.write(f"**Empregos Gerados:** {empregos:,.0f}".replace(',', '.') if pd.notna(empregos) else "Não informado")
            st.write(f"**População Beneficiada:** {populacao:,.0f}".replace(',', '.') if pd.notna(populacao) else "Não informado")
            
            if pd.notna(empregos) and pd.notna(populacao) and empregos > 0 and populacao > 0:
                taxa = (empregos / populacao * 100)
                st.write(f"**Taxa Emprego/Pop:** {taxa:.2f}%")
        
        with col3:
            st.markdown("**Datas**")
            st.write(f"**Data Cadastro:** {projeto['dataCadastro'].strftime('%d/%m/%Y') if pd.notna(projeto['dataCadastro']) else 'N/A'}")
            st.write(f"**Início Previsto:** {projeto['dataInicialPrevista'].strftime('%d/%m/%Y') if pd.notna(projeto['dataInicialPrevista']) else 'N/A'}")
            st.write(f"**Fim Previsto:** {projeto['dataFinalPrevista'].strftime('%d/%m/%Y') if pd.notna(projeto['dataFinalPrevista']) else 'N/A'}")
        
        st.markdown("---")
        
        # Descrição e outros detalhes
        # Nota: A coluna tem um erro de digitação no banco: 'descricaoricao'
        if 'descricaoricao' in projeto.index and pd.notna(projeto['descricaoricao']) and projeto['descricaoricao']:
            st.markdown("**Descrição:**")
            st.write(projeto['descricaoricao'])
        
        if pd.notna(projeto['funcaoSocial']) and projeto['funcaoSocial']:
            st.markdown("**Função Social:**")
            st.write(projeto['funcaoSocial'])
        
        if pd.notna(projeto['metaGlobal']) and projeto['metaGlobal']:
            st.markdown("**Meta Global:**")
            st.write(projeto['metaGlobal'])

# TAB 5: Dados Brutos
with tab5:
    st.header("Dados Brutos")
    
    st.write(f"**Total de registros:** {len(df_filtrado)}")
    
    # Opção de download
    csv = df_filtrado.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name=f"projetos_df_filtrado_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )
    
    # Mostrar dados
    st.dataframe(df_filtrado, width='stretch', height=600)
    
    # Estatísticas descritivas
    st.subheader("Estatísticas Descritivas")
    st.write(df_filtrado.describe())

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p>Dashboard de Análise de Projetos de Investimento - Distrito Federal</p>
        <p>Dados: ObrasGov.br | Desenvolvido por Lucas Guimarães Borges</p>
    </div>
""", unsafe_allow_html=True)
