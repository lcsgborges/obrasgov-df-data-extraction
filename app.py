import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import sqlite3
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# Configuração da página
st.set_page_config(
    page_title="Dashboard - Atividade LabLivre",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo customizado
st.markdown("""
    <style>
    .main-header {
        font-size: 2rem;
        font-weight: bold;
        color: #2c3e50;
        text-align: center;
        padding: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Cache para carregar dados do banco
@st.cache_data
def load_data_from_db():
    try:
        conn = sqlite3.connect('data/projetosDF.db')
        
        # Query principal
        query = """
        SELECT 
            idUnico,
            nome,
            cep,
            endereco,
            descricao,
            funcaoSocial,
            metaGlobal,
            dataInicialPrevista,
            dataFinalPrevista,
            dataInicialEfetiva,
            dataFinalEfetiva,
            dataCadastro,
            especie,
            natureza,
            situacao,
            uf,
            quantidadeEmpregosGerados,
            descricaoPopulacaoBeneficiada,
            populacaoBeneficiada,
            observacoesPertinentes,
            ehModeladaPorBim,
            dataSituacao,
            nomeTomadores,
            nomeExecutores,
            nomeRepassadores,
            descricaoEixos,
            descricaoTipos,
            descricaoSubtipos,
            valorInvestimentoPrevistoFontesderecurso
        FROM projetos
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        # Converter colunas de data
        date_cols = ['dataInicialPrevista', 'dataFinalPrevista', 'dataInicialEfetiva', 
                     'dataFinalEfetiva', 'dataCadastro', 'dataSituacao']
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Converter colunas numéricas
        numeric_cols = ['quantidadeEmpregosGerados', 'populacaoBeneficiada', 
                       'valorInvestimentoPrevistoFontesderecurso']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados do banco: {e}")
        return pd.DataFrame()

# Carregar dados
df = load_data_from_db()

# Verificar se os dados foram carregados
if df.empty:
    st.error("Nenhum dado encontrado no banco de dados!")
    st.stop()

# =======================
# SIDEBAR - FILTROS
# =======================
st.sidebar.header("Filtros")

# Filtro por situação
situacoes = ['Todos'] + sorted(df['situacao'].dropna().unique().tolist())
situacao_selecionada = st.sidebar.selectbox("Situação do Projeto", situacoes)

# Filtro por espécie
especies = ['Todos'] + sorted(df['especie'].dropna().unique().tolist())
especie_selecionada = st.sidebar.selectbox("Espécie", especies)

# Filtro por natureza
naturezas = ['Todos'] + sorted(df['natureza'].dropna().unique().tolist())
natureza_selecionada = st.sidebar.selectbox("Natureza", naturezas)

# Filtro por data de cadastro
st.sidebar.subheader("Período de Cadastro")
if df['dataCadastro'].notna().any():
    data_min = df['dataCadastro'].min()
    data_max = df['dataCadastro'].max()
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        data_inicio = st.date_input("De", value=data_min, min_value=data_min, max_value=data_max)
    with col2:
        data_fim = st.date_input("Até", value=data_max, min_value=data_min, max_value=data_max)
else:
    data_inicio = None
    data_fim = None

# Filtro por busca de texto
st.sidebar.subheader("Busca por Nome")
busca_nome = st.sidebar.text_input("Digite o nome do projeto")

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

if busca_nome:
    df_filtrado = df_filtrado[
        df_filtrado['nome'].str.contains(busca_nome, case=False, na=False)
    ]

# =======================
# HEADER
# =======================
st.markdown('<h1 class="main-header">Dashboard de Projetos - Distrito Federal</h1>', unsafe_allow_html=True)
st.markdown("---")

# =======================
# MÉTRICAS PRINCIPAIS
# =======================
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        label="Total de Projetos",
        value=f"{len(df_filtrado):,}",
        delta=f"{len(df_filtrado) - len(df):,}" if len(df_filtrado) != len(df) else None
    )

with col2:
    valor_total = df_filtrado['valorInvestimentoPrevistoFontesderecurso'].sum()
    st.metric(
        label="Investimento Total",
        value=f"R$ {valor_total/1e9:.2f}B" if valor_total >= 1e9 else f"R$ {valor_total/1e6:.1f}M"
    )

with col3:
    empregos_total = df_filtrado['quantidadeEmpregosGerados'].sum()
    st.metric(
        label="Empregos Gerados",
        value=f"{int(empregos_total):,}"
    )

with col4:
    pop_total = df_filtrado['populacaoBeneficiada'].sum()
    st.metric(
        label="População Beneficiada",
        value=f"{int(pop_total/1e6):.1f}M" if pop_total >= 1e6 else f"{int(pop_total/1e3)}K"
    )

with col5:
    projetos_execucao = len(df_filtrado[df_filtrado['situacao'] == 'Em Execução'])
    st.metric(
        label="Em Execução",
        value=f"{projetos_execucao}"
    )

st.markdown("---")

# =======================
# TABS
# =======================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Visão Geral",
    "Análise Temporal",
    "Análise Financeira",
    "Detalhes dos Projetos",
    "Dados Brutos"
])

# =======================
# TAB 1: VISÃO GERAL
# =======================
with tab1:
    st.header("Visão Geral dos Projetos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Distribuição por situação
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
        # Distribuição por espécie (pizza)
        st.subheader("Distribuição por Espécie")
        if len(df_filtrado) > 0:
            especie_counts = df_filtrado['especie'].value_counts()
            
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
    
    # Top 10 tipos de projetos
    st.subheader("Top 10 Tipos de Projetos")
    top_tipos = df_filtrado['descricaoTipos'].value_counts().head(10).reset_index()
    top_tipos.columns = ['Tipo', 'Quantidade']
    
    fig = px.bar(
        top_tipos,
        x='Quantidade',
        y='Tipo',
        orientation='h',
        color='Quantidade',
        color_continuous_scale='Teal'
    )
    fig.update_layout(showlegend=False, height=400)
    st.plotly_chart(fig, use_container_width=True)

# =======================
# TAB 2: ANÁLISE TEMPORAL
# =======================
with tab2:
    st.header("Análise Temporal dos Projetos")
    
    # Filtrar dados com datas válidas
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
        st.info("Nenhum projeto com data de cadastro disponível para análise temporal.")

# =======================
# TAB 3: ANÁLISE FINANCEIRA
# =======================
with tab3:
    st.header("Análise Financeira e de Impacto")
    
    # Filtrar dados com valores válidos
    df_financeiro = df_filtrado[
        (df_filtrado['valorInvestimentoPrevistoFontesderecurso'].notna()) &
        (df_filtrado['valorInvestimentoPrevistoFontesderecurso'] > 0)
    ].copy()
    
    if len(df_financeiro) > 0:
        col1, col2 = st.columns(2)
        
        with col1:
            # Investimento por tipo de projeto
            st.subheader("Investimento por Tipo de Projeto")
            invest_tipo = df_financeiro.groupby('descricaoTipos')['valorInvestimentoPrevistoFontesderecurso'].sum()
            invest_tipo = invest_tipo.nlargest(10).reset_index()
            invest_tipo.columns = ['Tipo', 'Investimento']
            invest_tipo['Investimento_M'] = invest_tipo['Investimento'] / 1e6
            
            fig = px.bar(
                invest_tipo,
                x='Investimento_M',
                y='Tipo',
                orientation='h',
                labels={'Investimento_M': 'Investimento (R$ Milhões)', 'Tipo': 'Tipo de Projeto'}
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Investimento por eixo (pizza)
            st.subheader("Investimento por Eixo")
            invest_eixo = df_financeiro.groupby('descricaoEixos')['valorInvestimentoPrevistoFontesderecurso'].sum()
            invest_eixo = invest_eixo.nlargest(8)
            
            fig = px.pie(
                values=invest_eixo.values,
                names=invest_eixo.index,
                hole=0.3
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        # Relação: Investimento vs Empregos Gerados
        st.subheader("Relação: Investimento vs Empregos Gerados")
        df_impacto = df_financeiro[
            (df_financeiro['quantidadeEmpregosGerados'].notna()) &
            (df_financeiro['quantidadeEmpregosGerados'] > 0)
        ].copy()
        
        if len(df_impacto) > 0:
            df_impacto['invest_milhoes'] = df_impacto['valorInvestimentoPrevistoFontesderecurso'] / 1e6
            
            fig = px.scatter(
                df_impacto,
                x='invest_milhoes',
                y='quantidadeEmpregosGerados',
                size='quantidadeEmpregosGerados',
                color='situacao',
                hover_data=['nome'],
                labels={
                    'invest_milhoes': 'Investimento (R$ Milhões)',
                    'quantidadeEmpregosGerados': 'Empregos Gerados',
                    'situacao': 'Situação'
                }
            )
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Dados insuficientes para análise de impacto (empregos).")
        
        # Relação: Investimento vs População Beneficiada
        st.subheader("Relação: Investimento vs População Beneficiada")
        df_pop = df_financeiro[
            (df_financeiro['populacaoBeneficiada'].notna()) &
            (df_financeiro['populacaoBeneficiada'] > 0)
        ].copy()
        
        if len(df_pop) > 0:
            df_pop['invest_milhoes'] = df_pop['valorInvestimentoPrevistoFontesderecurso'] / 1e6
            df_pop['pop_milhares'] = df_pop['populacaoBeneficiada'] / 1e3
            
            fig = px.scatter(
                df_pop,
                x='invest_milhoes',
                y='pop_milhares',
                size='pop_milhares',
                color='situacao',
                hover_data=['nome'],
                labels={
                    'invest_milhoes': 'Investimento (R$ Milhões)',
                    'pop_milhares': 'População Beneficiada (Milhares)',
                    'situacao': 'Situação'
                }
            )
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Dados insuficientes para análise de impacto (população).")
        
        # Top 10 projetos por investimento
        st.subheader("Top 10 Projetos por Investimento")
        top_invest = df_financeiro.nlargest(10, 'valorInvestimentoPrevistoFontesderecurso')[
            ['nome', 'valorInvestimentoPrevistoFontesderecurso', 'situacao', 'descricaoTipos']
        ].copy()
        top_invest['Investimento (R$ Milhões)'] = top_invest['valorInvestimentoPrevistoFontesderecurso'] / 1e6
        top_invest = top_invest.drop(columns=['valorInvestimentoPrevistoFontesderecurso'])
        top_invest.columns = ['Projeto', 'Situação', 'Tipo', 'Investimento (R$ Milhões)']
        
        st.dataframe(
            top_invest,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Nenhum projeto com informações financeiras disponíveis.")

# =======================
# TAB 4: DETALHES DOS PROJETOS
# =======================
with tab4:
    st.header("Detalhes dos Projetos")
    
    # Selector de projeto
    if len(df_filtrado) > 0:
        projetos_nomes = df_filtrado['nome'].unique().tolist()
        projeto_selecionado = st.selectbox(
            "Selecione um projeto para ver detalhes:",
            options=projetos_nomes,
            index=0
        )
        
        # Buscar detalhes do projeto
        projeto = df_filtrado[df_filtrado['nome'] == projeto_selecionado].iloc[0]
        
        # Layout em colunas
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"### {projeto['nome']}")
            
            st.markdown(f"**Localização:** {projeto['endereco']}")
            if projeto['cep']:
                st.markdown(f"**CEP:** {projeto['cep']}")
            
            st.markdown("---")
            
            st.markdown("**Descrição:**")
            st.write(projeto['descricao'] if pd.notna(projeto['descricao']) else "Não informado")
            
            if pd.notna(projeto['funcaoSocial']) and projeto['funcaoSocial'] != 'Não informado':
                st.markdown("**Função Social:**")
                st.write(projeto['funcaoSocial'])
            
            if pd.notna(projeto['metaGlobal']) and projeto['metaGlobal'] != 'Não informado':
                st.markdown("**Meta Global:**")
                st.write(projeto['metaGlobal'])
        
        with col2:
            st.markdown("#### Informações Gerais")
            
            st.markdown(f"**Situação:** {projeto['situacao']}")
            st.markdown(f"**Espécie:** {projeto['especie']}")
            st.markdown(f"**Natureza:** {projeto['natureza']}")
            
            st.markdown("---")
            
            if pd.notna(projeto['valorInvestimentoPrevistoFontesderecurso']):
                valor = projeto['valorInvestimentoPrevistoFontesderecurso']
                st.metric("Investimento Previsto", f"R$ {valor/1e6:.2f}M")
            
            if pd.notna(projeto['quantidadeEmpregosGerados']) and projeto['quantidadeEmpregosGerados'] > 0:
                st.metric("Empregos Gerados", f"{int(projeto['quantidadeEmpregosGerados']):,}")
            
            if pd.notna(projeto['populacaoBeneficiada']) and projeto['populacaoBeneficiada'] > 0:
                pop = projeto['populacaoBeneficiada']
                st.metric("População Beneficiada", f"{int(pop):,}")
        
        # Datas
        st.markdown("---")
        st.markdown("#### Cronograma")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if pd.notna(projeto['dataCadastro']):
                st.markdown(f"**Cadastro:**  \n{projeto['dataCadastro'].strftime('%d/%m/%Y')}")
        
        with col2:
            if pd.notna(projeto['dataInicialPrevista']):
                st.markdown(f"**Início Previsto:**  \n{projeto['dataInicialPrevista'].strftime('%d/%m/%Y')}")
        
        with col3:
            if pd.notna(projeto['dataFinalPrevista']):
                st.markdown(f"**Fim Previsto:**  \n{projeto['dataFinalPrevista'].strftime('%d/%m/%Y')}")
        
        with col4:
            if pd.notna(projeto['dataInicialEfetiva']):
                st.markdown(f"**Início Efetivo:**  \n{projeto['dataInicialEfetiva'].strftime('%d/%m/%Y')}")
        
        # Atores
        st.markdown("---")
        st.markdown("#### Atores Envolvidos")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if pd.notna(projeto['nomeTomadores']) and projeto['nomeTomadores'] != 'Não informado':
                st.markdown("**Tomadores:**")
                st.write(projeto['nomeTomadores'])
        
        with col2:
            if pd.notna(projeto['nomeExecutores']) and projeto['nomeExecutores'] != 'Não informado':
                st.markdown("**Executores:**")
                st.write(projeto['nomeExecutores'])
        
        with col3:
            if pd.notna(projeto['nomeRepassadores']) and projeto['nomeRepassadores'] != 'Não informado':
                st.markdown("**Repassadores:**")
                st.write(projeto['nomeRepassadores'])
        
        # Classificação
        st.markdown("---")
        st.markdown("#### Classificação")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if pd.notna(projeto['descricaoEixos']):
                st.markdown(f"**Eixo:**  \n{projeto['descricaoEixos']}")
        
        with col2:
            if pd.notna(projeto['descricaoTipos']):
                st.markdown(f"**Tipo:**  \n{projeto['descricaoTipos']}")
        
        with col3:
            if pd.notna(projeto['descricaoSubtipos']):
                st.markdown(f"**Subtipo:**  \n{projeto['descricaoSubtipos']}")
        
        # Observações
        if pd.notna(projeto['observacoesPertinentes']) and projeto['observacoesPertinentes'] != 'Não informado':
            st.markdown("---")
            st.markdown("#### Observações")
            st.info(projeto['observacoesPertinentes'])
    else:
        st.info("Nenhum projeto disponível com os filtros aplicados.")

# =======================
# TAB 5: DADOS BRUTOS
# =======================
with tab5:
    st.header("Dados Brutos")
    
    st.markdown(f"**Total de registros:** {len(df_filtrado):,}")
    
    # Opção para baixar CSV
    csv = df_filtrado.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Baixar dados filtrados em CSV",
        data=csv,
        file_name=f"projetos_df_filtrado_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )
    
    # Mostrar dados
    st.dataframe(
        df_filtrado,
        use_container_width=True,
        height=600
    )
    
    st.subheader("Estatísticas Numéricas")
    
    colunas_numericas = df_filtrado.select_dtypes(include=[np.number]).columns.tolist()
    
    if colunas_numericas:
        st.dataframe(
            df_filtrado[colunas_numericas].describe(),
            use_container_width=True
        )
    else:
        st.info("Nenhuma coluna numérica disponível para estatísticas.")

# =======================
# FOOTER
# =======================
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #666; padding: 2rem 0;'>
        <p>Dados extraídos de: ObrasGov.br | Governo Federal</p>
        <p style='font-size: 1rem;'>Feito por Lucas Guimarães Borges</p>
    </div>
""", unsafe_allow_html=True)
