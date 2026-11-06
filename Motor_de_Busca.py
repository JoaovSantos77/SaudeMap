import pandas as pd 
import streamlit as st 
import altair as alt

#carregar os dados 
#df_estabelecimentos = pd.read_csv('tbEstabelecimento202605.csv', sep=';', encoding='latin1') #passa a variavel que vai receber os dados 
#df_municipios = pd.read_csv('tbMunicipio202605.csv', sep = ';', encoding = 'latin1')         #'pd.read.csv' pede para o pandas le o arquivo 
#1° o nome do arquivo que vai ser lido; 2° as colunas são separadas por ponto e vírgula (;); 3° encoding='latin1' define o tipo de caracteres do arquivo, necessário para ler acentos e caracteres especiais do português corretamente

df_equipamentos = pd.read_csv('tabnet_equipamentos_SP_existente.csv', sep=';', na_values='-')
df_equipamentos = df_equipamentos[df_equipamentos['Município'] != 'Total'] 
df_equipamentos= df_equipamentos.fillna(0)


df_equipamentos['COD_MUNICIPIO'] = df_equipamentos['Município'].str[:6].astype(int) # cria uma nova coluna 
df_equipamentos['NOME_DO_MUNICIPIO'] = df_equipamentos['Município'].str[7:]
#print(df_equipamentos[['Município', 'COD_MUNICIPIO', 'NOME_DO_MUNICIPIO']].tail())

df_ibge = pd.read_csv('Agregados_por_municipios_basico_BR.csv', sep=';', encoding='latin1')
df_ibge = df_ibge[df_ibge['CD_UF'] == 35] 

df_ibge = df_ibge[['CD_MUN','NM_MUN','v0001']]
df_ibge['COD_MUNICIPIO'] = df_ibge['CD_MUN']//10

df_saudemap = pd.merge(df_ibge,df_equipamentos, on='COD_MUNICIPIO', how='left')
df_saudemap= df_saudemap.fillna(0)
df_saudemap.columns = df_saudemap.columns.str.replace('.. ','')
df_saudemap['MAMOGRAFO'] = df_saudemap['MAMOGRAFO COM COMANDO SIMPLES'] + df_saudemap['MAMOGRAFO COM ESTEREOTAXIA'] + df_saudemap['MAMOGRAFO COMPUTADORIZADO']
df_saudemap['ULTRASSOM'] = df_saudemap['ULTRASSOM DOPPLER COLORIDO'] + df_saudemap['ULTRASSOM ECOGRAFO'] + df_saudemap['ULTRASSOM CONVENCIONAL']
df_saudemap['HEMODIALISE'] = df_saudemap['APARELHO DE HEMODIALISE - AMBULATORIAL'] + df_saudemap['APARELHO DE HEMODIALISE - HOSPITALAR'] + df_saudemap['APARELHO DE HEMODIALISE RESERVA']





#print(df_estabelecimentos.head())#só para testar se estva funcionando

#print(df_estabelecimentos.columns.tolist())#colums = pega os nomes das colunas ; tolist = transforma em lista para ficar mais facil de ler 

# seleciona apenas as colunas que vamos usar no projeto
# CO_UNIDADE = chave para ligar o estabelecimento com os equipamentos (rlEstabEquipamento)
# telefone, endereço e bairro sairam porque agora a analise é por municipio, não por unidade
#df_estabelecimentos = df_estabelecimentos[['CO_UNIDADE', 'NO_FANTASIA', 'CO_MUNICIPIO_GESTOR', 'CO_ESTADO_GESTOR', 'NU_LATITUDE', 'NU_LONGITUDE']]

#print(df_municipios.columns.tolist())

# seleciona apenas as colunas que vamos usar do arquivo de municípios
#df_municipios = df_municipios[['CO_MUNICIPIO', 'NO_MUNICIPIO', 'CO_SIGLA_ESTADO']]

#junta(merge) os dados de estabelecimentos com os de municipio usando o código do municipio como chave 
#df_estabelecimentos = pd.merge(df_estabelecimentos, df_municipios, left_on='CO_MUNICIPIO_GESTOR', right_on='CO_MUNICIPIO', how='left')

# pd.merge → junta dois dataframes
# df_estabelecimentos e df_municipios → os dois arquivos que vamos juntar
# left_on='CO_MUNICIPIO_GESTOR' → coluna do primeiro arquivo que vai servir de chave
# right_on='CO_MUNICIPIO' → coluna do segundo arquivo que vai servir de chave
# how='left' → mantém todos os estabelecimentos mesmo que não tenha município correspondente

#PROXIMO PASSO: ler o rlEstabEquipamento e ver as colunas
#df_equipamentos = pd.read_csv('rlEstabEquipamento202605.csv', sep=';', encoding='latin1')
#print(df_equipamentos.columns.tolist())


#começando a parte visual do prjeto com streamlit

#comando para rodar o streamlit
#"streamlit run Motor_de_Busca.py"

#começando a parte visual do prjeto com streamlit

# configuração da página: título da aba do navegador e layout largo (cabe os cartões lado a lado)
# tem que ser o primeiro comando do streamlit no arquivo
st.set_page_config(page_title='SaúdeMap', page_icon='🏥', layout='wide')

# lista dos equipamentos: nome da coluna no dataframe -> nome bonito que aparece na tela
EQUIPAMENTOS = {
    'MAMOGRAFO': 'Mamógrafo',
    'HEMODIALISE': 'Hemodiálise',
    'ULTRASSOM': 'Ultrassom',
    'RESPIRADOR/VENTILADOR': 'Respirador/Ventilador',
    'TOMÓGRAFO COMPUTADORIZADO': 'Tomógrafo computadorizado',
    'RESSONANCIA MAGNETICA': 'Ressonância magnética',
}

# cores do gráfico (deixei aqui em cima para trocar fácil depois)
COR_BARRA = '#1351B4'     # azul das barras
COR_DESTAQUE = '#FFCD07'  # amarelo para destacar o município em foco
COR_REFERENCIA = '#C0392B'  # vermelho da linha da taxa do estado

MUNICIPIO_PADRAO = 'Cajamar'  # estudo de caso do projeto: o app abre com ele selecionado
UNIDADE = 'por 100 mil hab.'
FONTE = 'Fonte: CNES/DATASUS via TABNET (set/2026, equipamentos existentes) e IBGE, Censo 2022.'


def formata_br(numero, casas=2):
    # escreve o número no padrão brasileiro: 1.234,56
    texto = f'{numero:,.{casas}f}'
    return texto.replace(',', 'X').replace('.', ',').replace('X', '.')


def ranking_estado(equipamento):
    # monta o ranking dos 645 municípios para um equipamento
    # (usado nas duas abas, assim a aba 2 também sabe a posição de cada cidade no estado)
    df = df_saudemap[['NM_MUN', 'v0001']].copy()
    df['QUANTIDADE'] = df_saudemap[equipamento]
    df['TAXA_100MIL'] = df['QUANTIDADE'] / df['v0001'] * 100000

    # Ordena da maior taxa para a menor e renumera
    df = df.sort_values(by='TAXA_100MIL', ascending=False).reset_index(drop=True)
    df['POSICAO_ESTADO'] = df.index + 1
    return df


def taxa_do_estado(df):
    # taxa do estado inteiro: soma de todos os equipamentos / soma de toda a população
    return df['QUANTIDADE'].sum() / df['v0001'].sum() * 100000


def grafico_barras(df, altura_por_barra=28, taxa_referencia=None):
    # gráfico de barras horizontais feito com o Altair (já vem junto com o streamlit)
    # sort='-x' ordena da maior taxa para a menor, então não precisa mais do truque "01 - Nome"
    df = df.copy()
    df['TAXA_TEXTO'] = df['TAXA_100MIL'].apply(formata_br)

    maior_valor = df['TAXA_100MIL'].max()
    if taxa_referencia is not None:
        maior_valor = max(maior_valor, taxa_referencia)

    if taxa_referencia is not None:
        df['TAXA_REF'] = taxa_referencia

    base = alt.Chart(df).encode(
        y=alt.Y('NM_MUN:N', sort='-x', title=None, axis=alt.Axis(labelOverlap=False, labelLimit=200)),  # mostra o nome de todas as cidades
        # o domínio vai até 15% além da maior barra, para o número da ponta não ser cortado
        x=alt.X('TAXA_100MIL:Q', title=f'Equipamentos {UNIDADE}',
                scale=alt.Scale(domain=[0, max(maior_valor * 1.15, 1)])),
        tooltip=[
            alt.Tooltip('NM_MUN:N', title='Município'),
            alt.Tooltip('QUANTIDADE:Q', title='Quantidade'),
            alt.Tooltip('TAXA_TEXTO:N', title=f'Taxa {UNIDADE}'),
        ],
    )

    # barra amarela para o município em foco, azul para os outros
    barras = base.mark_bar().encode(
        color=alt.condition(
            alt.datum.NM_MUN == MUNICIPIO_FOCO,
            alt.value(COR_DESTAQUE),
            alt.value(COR_BARRA),
        )
    )

    # valor escrito na ponta de cada barra
    textos = base.mark_text(align='left', dx=4, color='#5B6573').encode(text='TAXA_TEXTO:N')

    grafico = barras + textos

    # linha vertical tracejada com a taxa do estado, para servir de referência
    # (usa os mesmos dados do gráfico, só que com a coluna TAXA_REF, que é igual em todas as linhas)
    if taxa_referencia is not None:
        linha = alt.Chart(df).mark_rule(color=COR_REFERENCIA, strokeDash=[6, 4], size=2).encode(x='mean(TAXA_REF):Q')
        grafico = barras + textos + linha

    altura = max(len(df) * altura_por_barra, 120)
    return grafico.properties(height=altura)


def destaca_foco(linha):
    # pinta de amarelo a linha do município em foco na tabela
    if linha['Município'] == MUNICIPIO_FOCO:
        return ['font-weight: bold; background-color: rgba(255, 205, 7, 0.25)'] * len(linha)
    return [''] * len(linha)


def formata_tabela(tabela, nome_equipamento):
    # números no padrão brasileiro + destaque do município em foco
    return (
        tabela.style
        .apply(destaca_foco, axis=1)
        .format({
            'População': lambda x: formata_br(x, 0),
            nome_equipamento: lambda x: formata_br(x, 0),
            f'Taxa {UNIDADE}': formata_br,
        })
    )



import json
import pydeck as pdk

COR_FUNDO_MENU = '#071D41'
OPCAO_NENHUM = 'Nenhum (visão geral do estado)'
ICONES = {'MAMOGRAFO': '🩻', 'HEMODIALISE': '🩸', 'ULTRASSOM': '📡',
          'RESPIRADOR/VENTILADOR': '🫁', 'TOMÓGRAFO COMPUTADORIZADO': '🌀', 'RESSONANCIA MAGNETICA': '🧲'}

# CSS: menu lateral azul escuro com texto branco e cartões brancos sobre o fundo claro
st.markdown(f"""
<style>
section[data-testid="stSidebar"] {{background-color: {COR_FUNDO_MENU};}}
section[data-testid="stSidebar"] * {{color: #FFFFFF;}}
section[data-testid="stSidebar"] div[data-baseweb="select"] * {{color: #071D41;}}
/* versões novas do Streamlit: garante texto escuro nas caixas de seleção do menu e esconde a bolinha do radio */
section[data-testid="stSidebar"] [data-baseweb="select"] div, section[data-testid="stSidebar"] [data-baseweb="select"] span, section[data-testid="stSidebar"] [data-baseweb="select"] input {{color:#071D41 !important; -webkit-text-fill-color:#071D41 !important;}}
section[data-testid="stSidebar"] [data-baseweb="select"] svg, section[data-testid="stSidebar"] [data-testid="stSelectbox"] [role="group"] svg {{color:#071D41 !important; fill:#071D41 !important;}}
section[data-testid="stSidebar"] [data-testid="stSelectbox"] [role="group"] input, section[data-testid="stSidebar"] [data-testid="stSelectbox"] [role="group"] button {{color:#071D41 !important; -webkit-text-fill-color:#071D41 !important;}}
section[data-testid="stSidebar"] [role="radiogroup"] label input[type="radio"] + div, section[data-testid="stSidebar"] [role="radiogroup"] label > div:first-of-type:not(:last-child) {{display:none !important;}}
[data-testid="stMain"] [data-testid="stColumn"] [data-testid="stVerticalBlockBorderWrapper"] {{background-color: #FFFFFF; border-radius: 12px;}}
.block-container {{padding-top: 2rem;}}
.mini {{border:1px solid #DCE3EE; border-radius:10px; padding:8px 12px; margin-bottom:8px; background:#FFFFFF;}}
.mini .n {{font-size:0.85rem; color:#5B6573;}}
.mini .v {{font-size:1.3rem; font-weight:700; color:#071D41;}}
/* menu: esconde a bolinha do st.radio e transforma cada opção num item de menu */
section[data-testid="stSidebar"] [role="radiogroup"] label > div:first-child {{display: none;}}
section[data-testid="stSidebar"] [role="radiogroup"] label {{padding: 10px 14px; border-radius: 8px; margin-bottom: 4px; width: 100%; cursor: pointer;}}
section[data-testid="stSidebar"] [role="radiogroup"] label:hover {{background-color: rgba(255,255,255,0.08);}}
section[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {{background-color: rgba(255,255,255,0.15); border-left: 4px solid #FFCD07; font-weight: 700;}}
.mini.sel {{border: 2px solid #FFCD07;}}
.up {{color:#168821; font-size:0.8rem;}} .down {{color:#E52207; font-size:0.8rem;}}
</style>
""", unsafe_allow_html=True)


@st.cache_data
def carrega_mapa():
    # malha dos municípios de SP (cada município é um polígono com o código IBGE de 7 dígitos)
    with open('sp_municipios.geojson', encoding='utf-8') as arquivo:
        return json.load(arquivo)


def cor_da_taxa(taxa, limite):
    # azul claro (taxa baixa) até azul escuro (taxa alta), no formato [vermelho, verde, azul]
    t = min(taxa / limite, 1) if limite > 0 else 0
    claro, escuro = (222, 235, 247), (8, 48, 107)
    return [round(claro[i] + (escuro[i] - claro[i]) * t) for i in range(3)]


def mapa_sp(df, destacar):
    # mapa de SP com o pydeck (já vem junto com o streamlit)
    # para cada polígono da malha, copiamos a taxa, o nome e a cor do município (ligação pelo código IBGE)
    malha = carrega_mapa()
    dados = df.set_index(df['CD_MUN'].astype(int).astype(str))
    limite_cor = df['TAXA_100MIL'].quantile(0.95)  # sem isso, um valor extremo deixa o mapa todo claro
    poligonos = []
    for feature in malha['features']:
        linha = dados.loc[feature['properties']['id']]
        em_destaque = linha['NM_MUN'] in destacar
        poligonos.append({
            'type': 'Feature', 'geometry': feature['geometry'],
            'properties': {
                'municipio': linha['NM_MUN'],
                'taxa': formata_br(linha['TAXA_100MIL']),
                'posicao': int(linha['POSICAO_ESTADO']),
                'cor': [255, 205, 7] if em_destaque else cor_da_taxa(linha['TAXA_100MIL'], limite_cor),
                'borda': 2 if em_destaque else 0.3,
            },
        })
    camada = pdk.Layer(
        'GeoJsonLayer', {'type': 'FeatureCollection', 'features': poligonos},
        get_fill_color='properties.cor', get_line_color=[7, 29, 65], get_line_width='properties.borda',
        line_width_units='pixels', stroked=False, pickable=True, auto_highlight=True,
    )
    # um retângulo do tamanho do mundo, na cor do fundo da página, por baixo de SP:
    # assim o mapa de fundo (outros estados e países) fica escondido e só aparece o estado de SP
    fundo = pdk.Layer(
        'PolygonLayer', [{'contorno': [[-179, -85], [179, -85], [179, 85], [-179, 85]]}],
        get_polygon='contorno', get_fill_color=[240, 244, 250], stroked=False,
    )
    return pdk.Deck(
        layers=[fundo, camada],
        initial_view_state=pdk.ViewState(latitude=-22.3, longitude=-48.7, zoom=5.6, min_zoom=5, max_zoom=10),
        tooltip={'text': '{municipio}\nTaxa: {taxa} por 100 mil hab.\nPosição no estado: {posicao}º'},
    )


def ranking_completo(equipamento):
    # ranking do estado + código IBGE (o mapa precisa do código para achar o polígono)
    df = ranking_estado(equipamento)
    return df.merge(df_saudemap[['NM_MUN', 'CD_MUN']], on='NM_MUN', how='left')


# MENU LATERAL
with st.sidebar:
    st.markdown('## 🏥 SaúdeMap')
    st.caption('Equipamentos de saúde por 100 mil hab. nos 645 municípios de SP')
    lista_municipios = sorted(df_saudemap['NM_MUN'].unique())
    escolha = st.selectbox('🔍 Buscar município', [OPCAO_NENHUM] + lista_municipios,
                           index=lista_municipios.index(MUNICIPIO_PADRAO) + 1)
    equipamento = st.selectbox('Equipamento', list(EQUIPAMENTOS.keys()), format_func=lambda c: EQUIPAMENTOS[c])
    pagina = st.radio('Menu', ['📍 Município', '📊 Ranking dos 645 municípios', '🗺️ Comparar municípios'])
    st.divider()
    st.caption(FONTE)

MUNICIPIO_FOCO = None if escolha == OPCAO_NENHUM else escolha
nome_equipamento = EQUIPAMENTOS[equipamento]
df_ranking = ranking_completo(equipamento)
taxa_estado = taxa_do_estado(df_ranking)


# PÁGINA MUNICÍPIO
if pagina == '📍 Município':
    if MUNICIPIO_FOCO is None:
        st.title('Estado de São Paulo')
        st.caption(f'{nome_equipamento} {UNIDADE} · taxa do estado: {formata_br(taxa_estado)}')
        st.pydeck_chart(mapa_sp(df_ranking, []), height=430)
    else:
        linha = df_ranking[df_ranking['NM_MUN'] == MUNICIPIO_FOCO].iloc[0]
        st.title(f'📍 {MUNICIPIO_FOCO}')
        abaixo = sum(
            ranking_estado(c).set_index('NM_MUN').loc[MUNICIPIO_FOCO, 'TAXA_100MIL'] < taxa_do_estado(ranking_estado(c))
            for c in EQUIPAMENTOS)
        st.caption(f'{formata_br(linha["v0001"], 0)} habitantes (IBGE 2022)')

        # resumo da cidade nos 6 equipamentos (a ficha ao lado do mapa mostra cada um)
        resumo = []
        for col in EQUIPAMENTOS:
            r = ranking_estado(col)
            l = r[r['NM_MUN'] == MUNICIPIO_FOCO].iloc[0]
            resumo.append((col, l, taxa_do_estado(r)))
        # a melhor posição só conta equipamentos que a cidade tem (com zero, a posição é só desempate)
        com_aparelho = [item for item in resumo if item[1]['QUANTIDADE'] > 0]
        melhor = min(com_aparelho, key=lambda item: item[1]['POSICAO_ESTADO']) if com_aparelho else None
        pior = max(resumo, key=lambda item: item[1]['POSICAO_ESTADO'])

        card1, card2, card3 = st.columns(3)
        with card1.container(border=True, height=150):
            st.metric('Abaixo da taxa do estado', f'{abaixo} de 6')
            st.caption('equipamentos com taxa menor que a média de SP')
        with card2.container(border=True, height=150):
            if melhor is not None:
                st.metric('🏆 Melhor posição no estado', f"{melhor[1]['POSICAO_ESTADO']}º de 645")
                st.caption(f'em {EQUIPAMENTOS[melhor[0]].lower()}')
            else:
                st.metric('🏆 Melhor posição no estado', '—')
                st.caption('a cidade não tem nenhum dos 6 equipamentos')
        # equipamentos que a cidade não tem nenhum aparelho
        # (a posição deles não diz nada: centenas de municípios estão empatados com zero)
        sem_aparelho = [EQUIPAMENTOS[col].lower() for col, l, ref in resumo if l['QUANTIDADE'] == 0]
        with card3.container(border=True, height=150):
            if sem_aparelho:
                st.metric('🚫 Sem nenhum aparelho', f'{len(sem_aparelho)} de 6')
                st.caption(', '.join(sem_aparelho))
            else:
                st.metric('⚠️ Pior posição no estado', f"{pior[1]['POSICAO_ESTADO']}º de 645")
                st.caption(f'em {EQUIPAMENTOS[pior[0]].lower()}')

        col_mapa, col_ficha = st.columns([3, 2])
        with col_mapa.container(border=True):
            st.markdown(f'**Mapa de SP · {nome_equipamento} {UNIDADE}** (🟡 {MUNICIPIO_FOCO})')
            st.pydeck_chart(mapa_sp(df_ranking, [MUNICIPIO_FOCO]), height=430)
        with col_ficha.container(border=True):
            st.markdown('**Os 6 equipamentos da cidade**')
            st.caption(f'Em amarelo: o equipamento escolhido no menu ({nome_equipamento}), que pinta o mapa.')
            for col, l, ref in resumo:
                d = l['TAXA_100MIL'] - ref
                classe = 'mini sel' if col == equipamento else 'mini'
                if l['QUANTIDADE'] == 0:
                    detalhe = 'nenhum aparelho'
                else:
                    detalhe = f"{int(l['QUANTIDADE'])} aparelho(s) · {l['POSICAO_ESTADO']}º no estado"
                txt = f'<span class="up">▲ acima do estado ({formata_br(ref)})</span>' if d >= 0 else f'<span class="down">▼ abaixo do estado ({formata_br(ref)})</span>'
                st.markdown(f"<div class='{classe}'><span class='n'>{ICONES[col]} {EQUIPAMENTOS[col]} · {detalhe}</span><br>"
                            f"<span class='v'>{formata_br(l['TAXA_100MIL'])}</span> {txt}</div>", unsafe_allow_html=True)


# PÁGINA RANKING
elif pagina == '📊 Ranking dos 645 municípios':
    st.title(f'📊 Ranking dos 645 municípios · {nome_equipamento}')
    st.caption(f'Quais municípios de SP têm mais {nome_equipamento.lower()} {UNIDADE}? A posição 1 é a maior taxa. '
               f'Taxa do estado de SP: {formata_br(taxa_estado)}. {FONTE}')
    col_graf, col_tab = st.columns(2)
    with col_graf.container(border=True):
        st.markdown('**Top 20 municípios**')
        st.altair_chart(grafico_barras(df_ranking.head(20), altura_por_barra=24), use_container_width=True)
    with col_tab.container(border=True):
        st.markdown('**Ranking completo (645 municípios)**')
        tabela1 = df_ranking[['POSICAO_ESTADO', 'NM_MUN', 'v0001', 'QUANTIDADE', 'TAXA_100MIL']].copy()
        tabela1.columns = ['Posição no estado', 'Município', 'População', nome_equipamento, f'Taxa {UNIDADE}']
        st.dataframe(formata_tabela(tabela1, nome_equipamento), hide_index=True, use_container_width=True, height=540)


# PÁGINA COMPARAR
else:
    st.title(f'🗺️ Comparar municípios · {nome_equipamento}')
    municipios = st.multiselect('Selecione as cidades:', lista_municipios,
                                default=[MUNICIPIO_FOCO] if MUNICIPIO_FOCO else [])
    if not municipios:
        st.info('Selecione pelo menos um município para comparar.')
    else:
        comp = df_ranking[df_ranking['NM_MUN'].isin(municipios)].reset_index(drop=True)
        comp['POSICAO_SELECAO'] = comp.index + 1
        if len(comp) <= 3:
            colunas = st.columns(3)
            for coluna, l in zip(colunas, comp.itertuples()):
                d = l.TAXA_100MIL - taxa_estado
                cor = 'red' if d < 0 else 'green'
                seta = '▼' if d < 0 else '▲'
                with coluna.container(border=True, height=200):
                    st.markdown(f'🟡 **{l.NM_MUN}** (em foco)' if l.NM_MUN == MUNICIPIO_FOCO else f'**{l.NM_MUN}**')
                    st.metric(f'Taxa {UNIDADE}', formata_br(l.TAXA_100MIL))
                    st.markdown(f':{cor}[{seta} {formata_br(d)} vs. estado ({formata_br(taxa_estado)})]')
        else:
            with st.container(border=True):
                st.altair_chart(grafico_barras(comp, altura_por_barra=45, taxa_referencia=taxa_estado), use_container_width=True)
                st.caption(f'A linha tracejada vermelha é a taxa do estado de SP ({formata_br(taxa_estado)} {UNIDADE}). '
                           f'Barras à direita dela: acima da média do estado. 🟡 = município em foco.')
        col_tab, col_mapa = st.columns([3, 2])
        with col_tab.container(border=True):
            tabela2 = comp[['POSICAO_SELECAO', 'NM_MUN', 'v0001', 'QUANTIDADE', 'TAXA_100MIL', 'POSICAO_ESTADO']].copy()
            tabela2['POSICAO_ESTADO'] = tabela2['POSICAO_ESTADO'].astype(str) + 'º'
            tabela2.columns = ['Posição na seleção', 'Município', 'População', nome_equipamento, f'Taxa {UNIDADE}', 'Posição no estado']
            st.dataframe(formata_tabela(tabela2, nome_equipamento), hide_index=True, use_container_width=True)
        with col_mapa.container(border=True):
            st.markdown('**Cidades selecionadas no mapa** 🟡')
            st.pydeck_chart(mapa_sp(df_ranking, municipios), height=360)
