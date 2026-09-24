import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURACIÓN DE LA PÁGINA (Layout)
st.set_page_config(page_title="Dashboard StreamView", layout="wide", initial_sidebar_state="expanded")

# 2. CARGA DE DATOS (Con caché para no recargar el Excel en cada clic)
@st.cache_data
def load_data():
    file_path = "StreamView_Analytics_Dataset.xlsx" # Asegúrate de que el Excel se llame exactamente así
    df_users = pd.read_excel(file_path, sheet_name='usuarios')
    df_subs = pd.read_excel(file_path, sheet_name='suscripciones')
    df_repro = pd.read_excel(file_path, sheet_name='reproducciones')
    df_content = pd.read_excel(file_path, sheet_name='contenidos')
    df_devices = pd.read_excel(file_path, sheet_name='dispositivos')
    return df_users, df_subs, df_repro, df_content, df_devices

df_users, df_subs, df_repro, df_content, df_devices = load_data()

# Preparación rápida de cruces de datos
df_churn = pd.merge(df_subs, df_users[['user_id']], on='user_id')
df_eng = pd.merge(df_repro, df_content[['content_id', 'genero']], on='content_id')
df_ux = pd.merge(df_repro, df_devices[['device_id', 'tipo_dispositivo']], on='device_id', how='left').dropna(subset=['tipo_dispositivo'])

# 3. BARRA LATERAL (Filtros Interactivos)
st.sidebar.title("Filtros Globales")
st.sidebar.markdown("Usa este panel para filtrar los datos del negocio.")
plan_seleccionado = st.sidebar.multiselect(
    "Seleccionar Plan:", 
    options=df_churn['plan'].unique(), 
    default=df_churn['plan'].unique()
)

# Filtrar datos según selección del usuario
df_churn_filtrado = df_churn[df_churn['plan'].isin(plan_seleccionado)]

# 4. ACTO 1: CONTEXTO (Tarjetas de KPI)
st.title("StreamView Analytics - Panel Ejecutivo")
st.markdown("---")

col1, col2, col3 = st.columns(3)
with col1:
    usuarios_activos = df_churn_filtrado[df_churn_filtrado['estado'] == 'Activa'].shape[0]
    st.metric(label="Usuarios Activos", value=f"{usuarios_activos:,}")
with col2:
    ingresos = df_churn_filtrado[df_churn_filtrado['estado'] == 'Activa']['precio_mensual_clp'].sum()
    st.metric(label="Ingresos MRR (CLP)", value=f"${ingresos:,.0f}")
with col3:
    if not df_churn_filtrado.empty:
        tasa_churn = (df_churn_filtrado[df_churn_filtrado['estado'] == 'Cancelada'].shape[0] / len(df_churn_filtrado)) * 100
    else:
        tasa_churn = 0
    st.metric(label="Tasa de Churn (Abandono)", value=f"{tasa_churn:.1f}%")

st.markdown("---")

# 5. ACTO 2: EL CONFLICTO (Zona Central)
col_izq, col_der = st.columns(2)

with col_izq:
    st.subheader("Fuga de Clientes por Plan")
    churn_grouped = df_churn_filtrado.groupby(['plan', 'estado']).size().reset_index(name='count')
    
    # Calcular porcentaje para el gráfico
    churn_grouped['porcentaje'] = churn_grouped.groupby('plan')['count'].transform(lambda x: x / x.sum() * 100)
    
    fig_churn = px.bar(churn_grouped, x='plan', y='porcentaje', color='estado', 
                       color_discrete_map={'Activa': '#2ca02c', 'Cancelada': '#d62728'},
                       barmode='stack', text_auto='.1f',
                       labels={'plan': 'Plan Contratado', 'porcentaje': 'Porcentaje (%)', 'estado': 'Estado de Cuenta'})
    st.plotly_chart(fig_churn, use_container_width=True)

with col_der:
    st.subheader("Fricción: Completitud por Dispositivo")
    ux_grouped = df_ux.groupby('tipo_dispositivo')['porcentaje_completado'].mean().reset_index().sort_values(by='porcentaje_completado', ascending=False)
    
    fig_ux = px.bar(ux_grouped, x='tipo_dispositivo', y='porcentaje_completado', 
                    color='porcentaje_completado', color_continuous_scale='magma',
                    labels={'tipo_dispositivo': 'Dispositivo', 'porcentaje_completado': 'Media Completada (%)'})
    # Fija el eje Y hasta el 100%
    fig_ux.update_yaxes(range=[0, 100])
    st.plotly_chart(fig_ux, use_container_width=True)

# 6. ACTO 3: LA RESOLUCIÓN (Zona Inferior)
st.markdown("---")
st.subheader("Oportunidades: Top Géneros por Engagement")

top_generos = df_eng.groupby('genero')['minutos_vistos'].sum().reset_index().sort_values(by='minutos_vistos', ascending=True).tail(5)
fig_generos = px.bar(top_generos, y='genero', x='minutos_vistos', orientation='h', 
                     color='minutos_vistos', color_continuous_scale='viridis',
                     labels={'minutos_vistos': 'Total Minutos Vistos', 'genero': 'Género del Contenido'})
st.plotly_chart(fig_generos, use_container_width=True)