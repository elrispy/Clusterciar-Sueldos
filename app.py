import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import io
from PIL import Image
from fpdf import FPDF
import tempfile
import os
from streamlit.components.v1 import iframe

# Configuración de la página
st.set_page_config(
    page_title="DDP 2025",
    layout="wide",
    menu_items={
        'Get Help': None,
        'Report a Bug': None,
        'About': None
    }
)

# CSS personalizado
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Red+Hat+Text:wght@400;500;700&display=swap');

    * {
        font-family = 'Red Hat Display', sans-serif !important;
    }

    .stApp {
        max-width: 100%;
        margin: 0 auto;
    }

    [data-testid="stSidebar"] {
        display: block !important;
        width: 250px !important;
        min-width: 250px !important;
        position: fixed;
        left: 0;
        top: 0;
        bottom: 0;
        background-color: #f8f9fa;
        padding: 20px;
        overflow-y: auto;
        z-index: 1000;
    }

    [data-testid="stAppViewContainer"] {
        margin-left: 270px !important;
        padding-right: 20px !important;
        width: calc(100% - 290px) !important;
    }

    .main-content {
        max-width: 1200px;
        margin: 0 auto;
        padding-left: 20px;
    }

    @media (max-width: 768px) {
        [data-testid="stSidebar"] {
            width: 100% !important;
            position: relative !important;
            height: auto !important;
            padding: 10px !important;
        }
        [data-testid="stAppViewContainer"] {
            margin-left: 0 !important;
            width: 100% !important;
            padding-right: 10px !important;
        }
        .main-content {
            padding-left: 10px !important;
        }
        .stButton>button {
            padding: 8px 16px;
            font-size: 14px;
        }
        .stSelectbox>select {
            padding: 8px;
            font-size: 14px;
        }
        .stTextInput>div>input {
            padding: 8px;
            font-size: 14px;
        }
        .stMetric {
            font-size: 12px !important;
        }
        .stMarkdown {
            font-size: 14px !important;
        }
        .altair-chart {
            width: 100% !important;
            height: auto !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Inicializar el estado de la sesión
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

# Credenciales estáticas
USERNAME = "admin"
PASSWORD = "ddp2025"

# Función para verificar las credenciales
def check_credentials(username, password):
    return username == USERNAME and password == PASSWORD

# Formulario de autenticación
def login_form():
    st.markdown("<h1 style='text-align: center;'>Iniciar Sesión - DDP 2025</h1>", unsafe_allow_html=True)
    with st.form(key="login_form"):
        username = st.text_input("Usuario", placeholder="Ingrese su usuario")
        password = st.text_input("Contraseña", type="password", placeholder="Ingrese su contraseña")
        submit_button = st.form_submit_button(label="Iniciar Sesión")
        
        if submit_button:
            if check_credentials(username, password):
                st.session_state.authenticated = True
                st.success("Inicio de sesión exitoso")
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos")

# Mostrar formulario de inicio de sesión si no está autenticado
if not st.session_state.authenticated:
    login_form()
else:
    # Cargar logo
    try:
        logo = Image.open("logo-clusterciar.png")
        st.image(logo, width=200)
    except FileNotFoundError:
        st.warning("No se encontró el archivo logo-clusterciar.png")

    # Función para mostrar el título principal
    def mostrar_titulo_principal():
        st.markdown("<h1 style='text-align: center;'>Dirección de Desarrollo de las Personas</h1>", unsafe_allow_html=True)

    # Menú principal
    st.title("DDP 2025")
    page = st.selectbox("Selecciona una página", [
        "Novedades DDP",
        "Indicadores",
        "Análisis de Legajos",
        "Sueldos FC",
        "Sueldos Todos",
        "Comparar Personas",
        "Tabla Salarial"
    ])

    # --- Página: Novedades DDP ---
    if page == "Novedades DDP":
        mostrar_titulo_principal()
        st.title("Novedades DDP")
        url = "https://informe-acciones-ddp-202-7ubaaqk.gamma.site/"
        iframe(url, height=600, scrolling=True)

        st.markdown("### Descargar Novedades")
        try:
            with open("DDP 2025.pdf", "rb") as f:
                st.download_button(
                    label="Descargar DDP 2025.pdf",
                    data=f.read(),
                    file_name="DDP 2025.pdf",
                    mime="application/pdf"
                )
        except FileNotFoundError:
            st.error("No se encontró el archivo DDP 2025.pdf. Asegúrate de que esté en el directorio raíz del repositorio.")

    # --- Página: Indicadores ---
    elif page == "Indicadores":
        mostrar_titulo_principal()
        st.title("Indicadores")
        url = "https://indicadores-ddp-l78n7xs.gamma.site/"
        iframe(url, height=600, scrolling=True)

        st.markdown("### Descargar Indicadores")
        try:
            with open("Indicadores DDP.pdf", "rb") as f:
                st.download_button(
                    label="Descargar Indicadores DDP.pdf",
                    data=f.read(),
                    file_name="Indicadores DDP.pdf",
                    mime="application/pdf"
                )
        except FileNotFoundError:
            st.error("No se encontró el archivo Indicadores DDP.pdf. Asegúrate de que esté en el directorio raíz del repositorio.")

    # --- Página: Análisis de Legajos ---
    elif page == "Análisis de Legajos":
        mostrar_titulo_principal()
        st.title("Análisis de Legajos")

        @st.cache_data
        def load_analisis_legajos():
            return pd.read_excel("Análisis de legajos.xlsx", sheet_name=0)

        try:
            df_legajos = load_analisis_legajos()
        except FileNotFoundError:
            st.error("No se encontró el archivo Análisis de legajos.xlsx")
            st.stop()

        df_legajos.columns = df_legajos.columns.str.strip().str.replace(' ', '_')
        categorical_columns = [col for col in df_legajos.columns if df_legajos[col].dtype == 'object']
        for col in categorical_columns:
            df_legajos[col] = df_legajos[col].astype(str).replace(['#Ref', 'nan'], '')

        date_columns = [col for col in df_legajos.columns if 'fecha' in col.lower() or 'date' in col.lower()]
        for col in date_columns:
            df_legajos[col] = pd.to_datetime(df_legajos[col], errors='coerce')

        # Filtros en el sidebar
        with st.sidebar:
            st.header("Filtros")
            filtros = {}
            for col in categorical_columns:
                if col in df_legajos.columns:
                    label = col.replace('_', ' ').title()
                    unique_values = [x for x in df_legajos[col].unique() if x]
                    filtros[col] = st.multiselect(label, unique_values, key=f"filter_{col}_legajos")
                else:
                    filtros[col] = []

        # Contenido principal
        with st.container():
            st.markdown('<div class="main-content">', unsafe_allow_html=True)
            
            df_filtered = df_legajos.copy()
            for key, values in filtros.items():
                if values:
                    df_filtered = df_filtered[df_filtered[key].isin(values)]

            st.subheader("Resumen General - Análisis de Legajos")
            if len(df_filtered) > 0:
                st.metric("Total Registros", len(df_filtered))
            else:
                st.info("No hay datos disponibles con los filtros actuales.")

            st.subheader("Tabla de Datos Filtrados")
            st.dataframe(df_filtered)

            csv = df_filtered.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Descargar datos filtrados como CSV",
                data=csv,
                file_name='analisis_legajos_filtrados.csv',
                mime='text/csv',
            )

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_filtered.to_excel(writer, index=False, sheet_name='Datos Filtrados')
            excel_data = output.getvalue()
            st.download_button(
                label="Descargar datos filtrados como Excel",
                data=excel_data,
                file_name='analisis_legajos_filtrados.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            )

            st.markdown('</div>', unsafe_allow_html=True)

    # --- Página: Sueldos FC ---
    elif page == "Sueldos FC":
        mostrar_titulo_principal()
        st.title("Análisis Salarial Personal Fuera de Convenio")

        @st.cache_data
        def load_data():
            return pd.read_excel("SUELDOS PARA INFORMES.xlsx", sheet_name=0)

        try:
            df = load_data()
        except FileNotFoundError:
            st.error("No se encontró el archivo SUELDOS PARA INFORMES.xlsx")
            st.stop()

        df.columns = df.columns.str.strip().str.replace(' ', '_').str.replace('%_BANDA_SALARIAL', 'Porcentaje_Banda_Salarial')
        categorical_columns = [
            'Empresa', 'CCT', 'Grupo', 'Comitente', 'Puesto', 'seniority', 'Gerencia', 'CVH',
            'Puesto_tabla_salarial', 'Locacion', 'Centro_de_Costos', 'Especialidad', 'Superior',
            'Personaapellido', 'Personanombre'
        ]
        for col in categorical_columns:
            if col in df.columns:
                df[col] = df[col].astype(str).replace(['#Ref', 'nan'], '')
            else:
                df[col] = ''

        date_columns = ['Fecha_de_Ingreso', 'Fecha_de_nacimiento']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')

        if 'Porcentaje_Banda_Salarial' in df.columns:
            df['Porcentaje_Banda_Salarial'] = pd.to_numeric(df['Porcentaje_Banda_Salarial'], errors='coerce')
            df['Porcentaje_Banda_Salarial'] = df['Porcentaje_Banda_Salarial'].apply(lambda x: x / 100 if x > 1 else x)

        # Filtros en el sidebar
        with st.sidebar:
            st.header("Filtros")
            filtros = {}
            filter_columns = [
                'Empresa', 'CCT', 'Grupo', 'Comitente', 'Puesto', 'seniority', 'Gerencia', 'CVH',
                'Puesto_tabla_salarial', 'Locacion', 'Centro_de_Costos', 'Especialidad', 'Superior',
                'Personaapellido', 'Personanombre'
            ]
            for col in filter_columns:
                if col in df.columns:
                    label = "Apellido" if col == "Personaapellido" else "Nombre" if col == "Personanombre" else col.replace('_', ' ').title()
                    unique_values = [x for x in df[col].dropna().unique() if x]
                    filtros[col] = st.multiselect(label, unique_values, key=f"filter_{col}_sueldos_fc")
                else:
                    filtros[col] = []

        # Contenido principal
        with st.container():
            st.markdown('<div class="main-content">', unsafe_allow_html=True)
            
            df_filtered = df.copy()
            for key, values in filtros.items():
                if values:
                    df_filtered = df_filtered[df_filtered[key].isin(values)]

            st.subheader("Resumen General - Sueldos para Informes")
            if len(df_filtered) > 0:
                promedio_sueldo = df_filtered['Total_sueldo_bruto'].mean() if 'Total_sueldo_bruto' in df_filtered.columns else 0
                minimo_sueldo = df_filtered['Total_sueldo_bruto'].min() if 'Total_sueldo_bruto' in df_filtered.columns else 0
                maximo_sueldo = df_filtered['Total_sueldo_bruto'].max() if 'Total_sueldo_bruto' in df_filtered.columns else 0
                dispersion_sueldo = maximo_sueldo - minimo_sueldo
                dispersion_porcentaje = (dispersion_sueldo / minimo_sueldo * 100) if minimo_sueldo > 0 else 0
                costo_total = df_filtered['Costo_laboral'].sum() if 'Costo_laboral' in df_filtered.columns else 0

                if 'Especialidad' in df_filtered.columns:
                    especialidad_dist = df_filtered['Especialidad'].value_counts(normalize=True) * 100
                    especialidad_dist = especialidad_dist.reset_index()
                    especialidad_dist.columns = ['Especialidad', 'Porcentaje']
                else:
                    especialidad_dist = pd.DataFrame()

                if 'Porcentaje_Banda_Salarial' in df_filtered.columns:
                    banda_25 = len(df_filtered[df_filtered['Porcentaje_Banda_Salarial'] < 0.25]) / len(df_filtered) * 100
                    banda_50 = len(df_filtered[df_filtered['Porcentaje_Banda_Salarial'] < 0.50]) / len(df_filtered) * 100
                    banda_75 = len(df_filtered[df_filtered['Porcentaje_Banda_Salarial'] < 0.75]) / len(df_filtered) * 100
                    banda_arriba_75 = len(df_filtered[df_filtered['Porcentaje_Banda_Salarial'] >= 0.75]) / len(df_filtered) * 100
                else:
                    banda_25 = banda_50 = banda_75 = banda_arriba_75 = 0

                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Total Personas", len(df_filtered))
                col2.metric("Sueldo Bruto Promedio", f"${promedio_sueldo:,.0f}")
                col3.metric("Sueldo Mínimo", f"${minimo_sueldo:,.0f}")
                col4.metric("Sueldo Máximo", f"${maximo_sueldo:,.0f}")

                col5, col6 = st.columns(2)
                col5.metric("Dispersión Salarial", f"${dispersion_sueldo:,.0f} ({dispersion_porcentaje:.1f}%)")
                col6.metric("Costo Laboral Total", f"${costo_total:,.0f}")

                if 'Porcentaje_Banda_Salarial' in df_filtered.columns:
                    st.markdown("### Distribución de Bandas Salariales")
                    banda_data = pd.DataFrame({
                        'Categoría': ['< 25%', '25-50%', '50-75%', '≥ 75%'],
                        'Porcentaje': [
                            banda_25,
                            banda_50 - banda_25,
                            banda_75 - banda_50,
                            banda_arriba_75
                        ]
                    })
                    banda_chart = alt.Chart(banda_data).mark_arc().encode(
                        theta=alt.Theta('Porcentaje:Q', stack=True),
                        color=alt.Color('Categoría:N', legend=alt.Legend(title="Banda Salarial")),
                        tooltip=['Categoría', alt.Tooltip('Porcentaje:Q', format='.1f')]
                    ).properties(width=300, height=300)
                    st.altair_chart(banda_chart, use_container_width=True)

                    st.markdown("**Porcentajes por Banda Salarial**:")
                    st.write(f"- Debajo del 25%: {banda_25:.1f}%")
                    st.write(f"- Debajo del 50%: {banda_50:.1f}%")
                    st.write(f"- Debajo del 75%: {banda_75:.1f}%")
                    st.write(f"- Arriba del 75%: {banda_arriba_75:.1f}%")

            else:
                st.info("No hay datos disponibles con los filtros actuales.")
                promedio_sueldo = minimo_sueldo = maximo_sueldo = dispersion_sueldo = dispersion_porcentaje = costo_total = 0
                banda_25 = banda_50 = banda_75 = banda_arriba_75 = 0
                especialidad_dist = pd.DataFrame()

            st.markdown("### Comparación por Categoría")
            agrupadores = [
                'Empresa', 'CCT', 'Grupo', 'Comitente', 'Puesto', 'seniority', 'Gerencia', 'CVH',
                'Puesto_tabla_salarial', 'Locacion', 'Centro_de_Costos', 'Especialidad', 'Superior'
            ]
            agrupadores = [col for col in agrupadores if col in df.columns]
            grupo_seleccionado = st.selectbox("Selecciona una categoría para agrupar", agrupadores, index=agrupadores.index('Puesto_tabla_salarial') if 'Puesto_tabla_salarial' in agrupadores else 0)

            if len(df_filtered) > 0:
                if 'Total_sueldo_bruto' in df_filtered.columns:
                    grouped_data = df_filtered.groupby(grupo_seleccionado).agg({
                        'Total_sueldo_bruto': ['mean', 'min', 'max'],
                        'seniority': 'count'
                    }).reset_index()
                    grouped_data.columns = [grupo_seleccionado, 'Sueldo_Promedio', 'Sueldo_Mínimo', 'Sueldo_Máximo', 'Cantidad']
                    grouped_data = grouped_data.dropna(subset=[grupo_seleccionado, 'Sueldo_Promedio'])
                    grouped_data[grupo_seleccionado] = grouped_data[grupo_seleccionado].astype(str)

                    chart = alt.Chart(grouped_data).mark_bar().encode(
                        x=alt.X(f"{grupo_seleccionado}:N", title=grupo_seleccionado, sort="-y"),
                        y=alt.Y("Sueldo_Promedio:Q", title="Sueldo Bruto Promedio"),
                        tooltip=[
                            grupo_seleccionado,
                            alt.Tooltip("Sueldo_Promedio:Q", title="Sueldo Promedio", format=",.0f"),
                            alt.Tooltip("Sueldo_Mínimo:Q", title="Sueldo Mínimo", format=",.0f"),
                            alt.Tooltip("Sueldo_Máximo:Q", title="Sueldo Máximo", format=",.0f")
                        ]
                    ).properties(height=400)
                    st.altair_chart(chart, use_container_width=True)

                if grupo_seleccionado == 'Puesto_tabla_salarial' and 'Puesto_tabla_salarial' in df_filtered.columns and 'seniority' in df_filtered.columns:
                    st.markdown("### Distribución de Seniority por Puesto Tabla Salarial")
                    puestos_opciones = ['Todos los puestos'] + sorted(df_filtered['Puesto_tabla_salarial'].unique().tolist())
                    puesto_seleccionado = st.selectbox("Selecciona un Puesto Tabla Salarial", puestos_opciones)
                    
                    gerencias = sorted(df_filtered['Gerencia'].unique().tolist())
                    gerencia_seleccionada = st.multiselect("Selecciona Gerencia(s)", gerencias, default=gerencias)

                    if puesto_seleccionado == 'Todos los puestos':
                        df_puesto = df_filtered[df_filtered['Gerencia'].isin(gerencia_seleccionada)]
                    else:
                        df_puesto = df_filtered[
                            (df_filtered['Puesto_tabla_salarial'] == puesto_seleccionado) &
                            (df_filtered['Gerencia'].isin(gerencia_seleccionada))
                        ]

                    if len(df_puesto) > 0:
                        seniority_dist = df_puesto['seniority'].value_counts(normalize=True) * 100
                        seniority_dist = seniority_dist.reset_index()
                        seniority_dist.columns = ['Seniority', 'Porcentaje']

                        seniority_chart = alt.Chart(seniority_dist).mark_arc().encode(
                            theta=alt.Theta('Porcentaje:Q', stack=True),
                            color=alt.Color('Seniority:N', legend=alt.Legend(title="Seniority")),
                            tooltip=['Seniority', alt.Tooltip('Porcentaje:Q', format='.1f')]
                        ).properties(width=300, height=300)
                        st.altair_chart(seniority_chart, use_container_width=True)

                        st.markdown("**Porcentajes de Seniority**:")
                        for _, row in seniority_dist.iterrows():
                            st.write(f"- {row['Seniority']}: {row['Porcentaje']:.1f}%")

                        if puesto_seleccionado != 'Todos los puestos' and 'Total_sueldo_bruto' in df_puesto.columns:
                            sueldo_stats = df_puesto['Total_sueldo_bruto'].agg(['min', 'mean', 'max']).round(0)
                            st.markdown(f"**Sueldos para {puesto_seleccionado} (filtrado por Gerencia)**:")
                            st.write(f"- Mínimo: ${sueldo_stats['min']:,.0f}")
                            st.write(f"- Promedio: ${sueldo_stats['mean']:,.0f}")
                            st.write(f"- Máximo: ${sueldo_stats['max']:,.0f}")
                    else:
                        st.warning("No hay datos para el puesto tabla salarial y gerencia seleccionados.")

                if grupo_seleccionado == 'seniority' and 'seniority' in df_filtered.columns and 'Total_sueldo_bruto' in df_filtered.columns:
                    sueldo_stats = grouped_data[['seniority', 'Sueldo_Mínimo', 'Sueldo_Promedio', 'Sueldo_Máximo']]
                    st.markdown("**Sueldos por Seniority**:")
                    st.dataframe(sueldo_stats)

                # Distribución de Especialidad (reubicada)
                if 'Especialidad' in df_filtered.columns:
                    st.markdown("### Distribución de Especialidad")
                    especialidad_chart = alt.Chart(especialidad_dist).mark_bar().encode(
                        x=alt.X('Porcentaje:Q', title='Porcentaje (%)'),
                        y=alt.Y('Especialidad:N', title='Especialidad', sort='-x'),
                        tooltip=['Especialidad', alt.Tooltip('Porcentaje:Q', format='.1f')]
                    ).properties(height=300)
                    st.altair_chart(especialidad_chart, use_container_width=True)

            else:
                st.warning("No hay datos para mostrar en el gráfico de comparación por categoría.")

            st.subheader("Tabla de Datos Filtrados")
            st.dataframe(df_filtered)

            csv = df_filtered.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Descargar datos filtrados como CSV",
                data=csv,
                file_name='sueldos_filtrados.csv',
                mime='text/csv',
            )

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_filtered.to_excel(writer, index=False, sheet_name='Datos Filtrados')
                resumen = pd.DataFrame({
                    'Total_personas': [len(df_filtered)],
                    'Sueldo_Promedio': [promedio_sueldo],
                    'Sueldo_Mínimo': [minimo_sueldo],
                    'Sueldo_Máximo': [maximo_sueldo],
                    'Dispersión_Salarial': [dispersion_sueldo],
                    'Costo_laboral': [costo_total],
                    'Porcentaje_<25%': [banda_25],
                    'Porcentaje_<50%': [banda_50],
                    'Porcentaje_<75%': [banda_75],
                    'Porcentaje_≥75%': [banda_arriba_75]
                })
                resumen.to_excel(writer, index=False, sheet_name='Resumen')
            excel_data = output.getvalue()
            st.download_button(
                label="Descargar reporte en Excel",
                data=excel_data,
                file_name='reporte_sueldos.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            )

            if st.button("Generar reporte en PDF"):
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=12)

                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
                        logo.save(tmpfile.name)
                        pdf.image(tmpfile.name, x=10, y=8, w=50)
                    os.unlink(tmpfile.name)
                except Exception as e:
                    pdf.cell(200, 10, txt="Logo no disponible", ln=True, align='C')

                pdf.ln(30)
                def clean_text(text):
                    return ''.join(c for c in str(text) if ord(c) < 128)

                pdf.cell(200, 10, txt=clean_text("Reporte de Sueldos - Sueldos para Informes"), ln=True, align='C')
                pdf.ln(10)
                pdf.cell(200, 10, txt=clean_text(f"Total personas: {len(df_filtered)}"), ln=True)
                pdf.cell(200, 10, txt=clean_text(f"Sueldo promedio: ${promedio_sueldo:,.0f}"), ln=True)
                pdf.cell(200, 10, txt=clean_text(f"Sueldo mínimo / máximo: ${minimo_sueldo:,.0f} / ${maximo_sueldo:,.0f}"), ln=True)
                pdf.cell(200, 10, txt=clean_text(f"Dispersión salarial: ${dispersion_sueldo:,.0f} ({dispersion_porcentaje:.1f}%)"), ln=True)
                pdf.cell(200, 10, txt=clean_text(f"Costo laboral total: ${costo_total:,.0f}"), ln=True)
                pdf.cell(200, 10, txt=clean_text(f"Porcentaje <25%: {banda_25:.1f}%"), ln=True)
                pdf.cell(200, 10, txt=clean_text(f"Porcentaje <50%: {banda_50:.1f}%"), ln=True)
                pdf.cell(200, 10, txt=clean_text(f"Porcentaje <75%: {banda_75:.1f}%"), ln=True)
                pdf.cell(200, 10, txt=clean_text(f"Porcentaje ≥75%: {banda_arriba_75:.1f}%"), ln=True)

                if len(df_filtered) < 20 and all(col in df_filtered.columns for col in ['Personaapellido', 'Personanombre', 'Puesto', 'Seniority', 'Porcentaje_Banda_Salarial', 'Total_sueldo_bruto']):
                    pdf.ln(20)
                    pdf.set_font("Arial", size=10)
                    pdf.cell(200, 10, txt="Detalles de Personas (ordenado por Total Sueldo Bruto descendente)", ln=True, align='C')
                    pdf.ln(5)

                    columns = ['Personaapellido', 'Personanombre', 'Puesto', 'Seniority', 'Porcentaje_Banda_Salarial', 'Total_sueldo_bruto']
                    df_table = df_filtered[columns].sort_values(by='Total_sueldo_bruto', ascending=False)
                    pdf.set_font("Arial", size=8)

                    for col in columns:
                        pdf.cell(33, 10, clean_text(col.replace('_', ' ').title()), border=1, align='C')
                    pdf.ln()

                    for index, row in df_table.iterrows():
                        pdf.cell(33, 10, clean_text(str(row['Personaapellido'])), border=1)
                        pdf.cell(33, 10, clean_text(str(row['Personanombre'])), border=1)
                        pdf.cell(33, 10, clean_text(str(row['Puesto'])), border=1)
                        pdf.cell(33, 10, clean_text(str(row['Seniority'])), border=1)
                        pdf.cell(33, 10, clean_text(f"{row['Porcentaje_Banda_Salarial']*100:.1f}%"), border=1)
                        pdf.cell(35, 10, clean_text(f"${row['Total_sueldo_bruto']:,.0f}"), border=1)
                        pdf.ln()

                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
                        pdf.output(tmpfile.name)
                        with open(tmpfile.name, "rb") as f:
                            st.download_button(
                                label="Descargar reporte en PDF",
                                data=f.read(),
                                file_name="reporte_sueldos.pdf",
                                mime="application/pdf"
                            )
                    os.unlink(tmpfile.name)
                except Exception as e:
                    st.error(f"Error al generar el PDF: {str(e)}")

            st.markdown("### Conclusión Final")
            if len(df_filtered) > 0:
                conclusion = f"""
                - Se analizaron **{len(df_filtered)}** empleados.
                - El sueldo bruto promedio es **${promedio_sueldo:,.0f}**.
                - El costo laboral total asciende a **${costo_total:,.0f}**.
                - La distribución de bandas salariales muestra que:
                  - **{banda_25:.1f}%** está por debajo del 25% de la banda.
                  - **{banda_50:.1f}%** está por debajo del 50%.
                  - **{banda_75:.1f}%** está por debajo del 75%.
                  - **{banda_arriba_75:.1f}%** está por encima del 75%.
                - **Recomendación**: Revisar los puestos con alta dispersión salarial y seniority bajo para ajustar políticas de compensación.
                """
                st.markdown(conclusion)
            else:
                st.markdown("No hay datos suficientes para generar una conclusión. Ajuste los filtros para incluir más datos.")

            st.markdown('</div>', unsafe_allow_html=True)

    # --- Página: Sueldos Todos ---
    elif page == "Sueldos Todos":
        mostrar_titulo_principal()
        st.title("Análisis Salarial Personal Clusterciar")

        @st.cache_data
        def load_sueldos_data():
            try:
                return pd.read_excel("sueldos.xlsx", sheet_name=0)
            except Exception as e:
                st.error(f"Error al intentar cargar sueldos.xlsx: {str(e)}")
                return None

        df = load_sueldos_data()
        if df is None:
            st.error("No se pudo cargar el archivo sueldos.xlsx. Verifica que el archivo exista y sea accesible.")
            st.stop()

        df.columns = df.columns.str.strip().str.replace(' ', '_').lower()
        if 'convenio' in df.columns:
            df = df.rename(columns={'convenio': 'categoria'})

        categorical_columns = ['categoria', 'es_cvh', 'personaapellido', 'personanombre', 'comitente']
        for col in categorical_columns:
            if col in df.columns:
                df[col] = df[col].astype(str).replace(['#Ref', 'Sin dato'], 'Sin dato')
            else:
                df[col] = 'Sin dato'

        df['apellido_nombre'] = df['personaapellido'] + ' ' + df['personanombre']
        numeric_columns = ['total_sueldo_bruto', 'neto', 'total_costo_laboral']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0))
            else:
                df[col] = 0

        st.subheader("Filtros")
        filtros = {}
        filter_columns = ['empresa', 'es_cvh', 'apellido_y_nombre', 'comitente']
        for col in filter_columns:
            if col in df.columns:
                unique_values = [x for x in df[col].dropna().unique() if str(x).strip() != 'Sin dato']
                if len(unique_values) > 0:
                    label = col.replace('_', ' ').title()
                    filtros[col] = st.multiselect(f"{label}", unique_values, key=f"filter_{col}_sueldos")
                else:
                    filtros[col] = []
            else:
                filtros[col] = []

        df_filtered = df.copy()
        for key, values in filtros.items():
            if values:
                df_filtered = df_filtered[df_filtered[key].isin(values)]

        st.subheader("Resumen General - Sueldos")
        if len(df_filtered) > 0:
            cantidad_personas = len(df_filtered)
            total_sueldo_bruto = df_filtered['total_sueldo_bruto'].sum()
            total_sueldo_neto = df_filtered['neto'].sum()
            total_costo_laboral = df_filtered['total_costo_laboral'].sum()
            sueldo_bruto_promedio = total_sueldo_bruto / cantidad_personas if cantidad_personas > 0 else 0
            sueldo_neto_promedio = total_sueldo_neto / cantidad_personas if cantidad_personas > 0 else 0
            costo_laboral_promedio = total_costo_laboral / cantidad_personas if cantidad_personas > 0 else 0

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Cantidad de Personas", cantidad_personas)
            col2.metric("Total Sueldo Bruto", f"${total_sueldo_bruto:,.0f}")
            col3.metric("Total Sueldo Neto", f"${total_sueldo_neto:,.0f}")
            col4.metric("Total Costo Laboral", f"${total_costo_laboral:,.0f}")

            col5, col6, col7 = st.columns(3)
            col5.metric("Sueldo Bruto Promedio", f"${sueldo_bruto_promedio:,.0f}")
            col6.metric("Sueldo Neto Promedio", f"${sueldo_neto_promedio:,.0f}")
            col7.metric("Costo Laboral Promedio", f"${costo_laboral_promedio:,.0f}")

            st.subheader("Tabla de Datos Filtrados")
            display_columns = ['empresa', 'es_cvh', 'apellido_y_nombre', 'comitente', 'total_sueldo_bruto', 'neto', 'total_costo_laboral']
            st.dataframe(df_filtered[display_columns].rename(columns={
                'empresa': 'Empresa',
                'es_cvh': 'Cvh',
                'apellido_y_nombre': 'Apellido y Nombre',
                'comitente': 'Comitente',
                'total_sueldo_bruto': 'Total Sueldo Bruto',
                'neto': 'Neto',
                'total_costo_laboral': 'Total Costo Laboral'
            }))

            csv = df_filtered[display_columns].to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Descargar datos filtrados como CSV",
                data=csv,
                file_name='sueldos_filtrados.csv',
                mime='text/csv',
            )

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_filtered[display_columns].to_excel(writer, index=False, sheet_name='Datos Filtrados')
            excel_data = output.getvalue()
            st.download_button(
                label="Descargar datos filtrados como Excel",
                data=excel_data,
                file_name='sueldos_filtrados.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            )
        else:
            st.info("No hay datos disponibles con los filtros actuales.")

    # --- Página: Comparar Personas ---
    elif page == "Comparar Personas":
        mostrar_titulo_principal()
        st.title("Comparar Personas")

        @st.cache_data
        def load_data():
            try:
                return pd.read_excel("SUELDOS PARA INFORMES.xlsx", sheet_name=0)
            except FileNotFoundError:
                st.error("No se encontró el archivo SUELDOS PARA INFORMES.xlsx. Asegúrate de que esté en el directorio raíz del repositorio.")
                return None
            except Exception as e:
                st.error(f"Error al cargar SUELDOS PARA INFORMES.xlsx: {str(e)}")
                return None

        df = load_data()
        if df is None:
            st.stop()

        df.columns = df.columns.str.strip().str.replace(' ', '_')
        required_columns = ['Gerencia', 'Puesto_tabla_salarial', 'Grupo', 'seniority', 'Personaapellido', 'Personanombre']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            st.error(f"Faltan las siguientes columnas en el archivo SUELDOS PARA INFORMES.xlsx: {missing_columns}")
            st.stop()

        categorical_columns = [
            'Empresa', 'CCT', 'Grupo', 'Comitente', 'Puesto', 'seniority', 'Gerencia', 'CVH',
            'Puesto_tabla_salarial', 'Locacion', 'Centro_de_Costos', 'Especialidad', 'Superior',
            'Personaapellido', 'Personanombre'
        ]
        for col in categorical_columns:
            if col in df.columns:
                df[col] = df[col].astype(str).replace(['#Ref', 'nan', 'NaN', ''], 'Sin dato')
            else:
                df[col] = 'Sin dato'

        df['Apellido_y_Nombre'] = df['Personaapellido'] + ' ' + df['Personanombre']
        st.subheader("Filtros Previos")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            gerencias = ['Todas'] + sorted([x for x in df['Gerencia'].unique() if x != 'Sin dato'])
            selected_gerencia = st.selectbox("Selecciona una Gerencia", gerencias)
        with col2:
            puestos = ['Todos'] + sorted([x for x in df['Puesto_tabla_salarial'].unique() if x != 'Sin dato'])
            selected_puesto = st.selectbox("Selecciona un Puesto Tabla Salarial", puestos)
        with col3:
            grupos = ['Todos'] + sorted([x for x in df['Grupo'].unique() if x != 'Sin dato'])
            selected_grupo = st.selectbox("Selecciona un Grupo", grupos)
        with col4:
            seniorities = ['Todos'] + sorted([x for x in df['seniority'].unique() if x != 'Sin dato'])
            selected_seniority = st.selectbox("Selecciona un Seniority", seniorities)

        df_filtered = df.copy()
        if selected_gerencia != 'Todas':
            df_filtered = df_filtered[df_filtered['Gerencia'] == selected_gerencia]
        if selected_puesto != 'Todos':
            df_filtered = df_filtered[df_filtered['Puesto_tabla_salarial'] == selected_puesto]
        if selected_grupo != 'Todos':
            df_filtered = df_filtered[df_filtered['Grupo'] == selected_grupo]
        if selected_seniority != 'Todos':
            df_filtered = df_filtered[df_filtered['seniority'] == selected_seniority]

        if len(df_filtered) == 0:
            st.warning("No hay datos disponibles con los filtros seleccionados. Por favor, ajusta los filtros o verifica que el archivo SUELDOS PARA INFORMES.xlsx contenga datos válidos.")
            st.stop()

        st.subheader("Selección para comparar")
        comparison_type = st.selectbox(
            "Tipo de comparación",
            ["Comparar dos personas", "Comparar todas las personas filtradas"]
        )

        if comparison_type == "Comparar dos personas":
            nombres_completos = sorted([x for x in df_filtered['Apellido_y_Nombre'].unique() if x != 'Sin dato Sin dato'])
            if not nombres_completos:
                st.warning("No hay nombres completos disponibles para comparar. Verifica los datos en las columnas 'Personaapellido' y 'Personanombre'.")
                st.stop()
            col1, col2 = st.columns(2)
            with col1:
                persona_1 = st.selectbox("Selecciona Apellido y Nombre", nombres_completos, key="persona_1")
            with col2:
                persona_2 = st.selectbox("Selecciona Apellido y Nombre", nombres_completos, key="persona_2")

            df_persona_1 = df_filtered[df_filtered['Apellido_y_Nombre'] == persona_1]
            df_persona_2 = df_filtered[df_filtered['Apellido_y_Nombre'] == persona_2]

            if not df_persona_1.empty and not df_persona_2.empty:
                st.markdown("### Comparativa de Personas")
                metrics = ['Apellido_y_Nombre', 'Total_sueldo_bruto', 'seniority', 'Puesto', 'Gerencia']
                comparison_data = []
                for df_persona, label in [(df_persona_1, "Persona 1"), (df_persona_2, "Persona 2")]:
                    row = df_persona.iloc[0]
                    data = {metric: row[metric] if metric in df_persona.columns else "N/A" for metric in metrics}
                    data['Label'] = label
                    comparison_data.append(data)

                comparison_df = pd.DataFrame(comparison_data)
                st.dataframe(comparison_df.set_index('Label')[metrics])

                if 'Total_sueldo_bruto' in df_persona_1.columns and 'Total_sueldo_bruto' in df_persona_2.columns:
                    sueldo_1 = float(df_persona_1['Total_sueldo_bruto'].iloc[0])
                    sueldo_2 = float(df_persona_2['Total_sueldo_bruto'].iloc[0])
                    if sueldo_1 != 0:
                        diferencia_porcentual = ((sueldo_2 - sueldo_1) / sueldo_1) * 100
                        st.markdown(f"**Diferencia porcentual en sueldo bruto:** {diferencia_porcentual:.2f}%")
                        if diferencia_porcentual > 0:
                            st.write(f"El sueldo de {persona_2} es {diferencia_porcentual:.2f}% mayor que el de {persona_1}.")
                        elif diferencia_porcentual < 0:
                            st.write(f"El sueldo de {persona_2} es {abs(diferencia_porcentual):.2f}% menor que el de {persona_1}.")
                        else:
                            st.write("Ambas personas tienen el mismo sueldo bruto.")
                    else:
                        st.warning("No se puede calcular la diferencia porcentual porque el sueldo de la primera persona es 0.")
            else:
                st.warning("Una o ambas personas seleccionadas no tienen datos disponibles.")

        else:
            st.markdown("### Comparativa de Todas las Personas Filtradas")
            if len(df_filtered) > 0 and 'Total_sueldo_bruto' in df_filtered.columns:
                df_filtered['Nombre_Completo'] = df_filtered['Apellido_y_Nombre']
                df_filtered = df_filtered.sort_values(by='Total_sueldo_bruto', ascending=False)

                chart = alt.Chart(df_filtered).mark_bar().encode(
                    x=alt.X('Nombre_Completo:N', title='Persona', sort='-y', axis=alt.Axis(labelAngle=45)),
                    y=alt.Y('Total_sueldo_bruto:Q', title='Sueldo Bruto ($)''),
                    tooltip=[
                        'Nombre_Completo',
                        alt.Tooltip('Total_sueldo_bruto:Q', title='Sueldo Bruto', format='$,.0f'),
                        st'P',
                        'Gerencia',
                        'seniority'
                    ]
                ).properties(
                    height=400,
                    title='Sueldos Brutos de las Personas Filtradas (de Mayor a Menor)'
                )
                st.altair_chart(chart, use_container_width=True)

                st.subheader("Datos Detallados")
                display_columns = ['Nombre_Completo', 'Total_sueldo_bruto', 'seniority', 'Puesto', 'Gerencia']
                st.dataframe(df_filtered[display])

            else:
                st.warning("No hay datos disponibles para comparar con los filtros seleccionados.")

    # --- Página: Tabla Salarial ---
    elif page == "Tabla Salarial":
        mostrar_titulo_principal()
        st.title("Consulta de Tabla Salarial")

        @st.cache_data
        def load_tabla_salarial():
            return pd.read_excel("tabla salarial.xlsx", sheet_name=0)

        try:
            df_tabla = load_tabla_salarial()
        except FileNotFoundError:
            st.error("No se encontró el archivo tabla salarial.xlsx")
            st.stop()

git add app.py
git commit -m "Fix Tabla Salarial column handling"
git push origin main

        puestos = sorted(df_tabla['Puesto'].unique())
        seniorities = sorted(df_tabla['Seniority'].unique())
        locaciones = sorted(df_tabla['Locacion'].unique())

        st.subheader("Comparativa de Valores Salariales")
        st.markdown("**Primera Selección**")
        col1, col2, col3 = st.columns(3)
        with col1:
            selected_puesto_1 = st.selectbox("Selecciona un Puesto (1)", puestos, key="puesto_1")
        with col2:
            selected_seniority_1 = st.selectbox("Selecciona un Seniority (1)", seniorities, key="seniority_1")
        with col3:
            selected_locacion_1 = st.selectbox("Selecciona una Locación (1)", locaciones, key="locacion_1")

        df_selected_1 = df_tabla[
            (df_tabla['Puesto'] == selected_puesto_1) &
            (df_tabla['Seniority'] == selected_seniority_1) &
            (df_tabla['Locacion'] == selected_locacion_1]
        )

        if not df_selected_1.empty:
            st.markdown(f"**Valores Salariales para {selected_puesto_1} - {selected_seniority_1} - {selected_locacion_1}**")
            valores_1 = df_selected_1[['Q1', 'Q2', 'Q3', 'Q4', 'Q5']].iloc[0]
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("Q1", f"${valores_1['Q1']:,.0f}")
            col2.metric("Q2", f"${valores_1['Q2']:,.0f}")
            col3.metric("Q3", f"${valores_1['Q3']:,.0f}")
            col4.metric("Q4", f"${valores_1['Q4']:,.0f}")
            col5.metric("Q5", f"${valores_1['Q5']:,.0f}")
        else:
            st.warning(f"No se encontraron datos para {selected_puesto_1} con Seniority {selected_seniority_1} en Locación {selected_locacion_1}.")
            valores_1 = None

        st.markdown("**Segunda Selección**")
        col1, col2, col3 = st.columns(3)
        with col1:
            selected_puesto_2 = st.selectbox("Selecciona un Puesto (2)", puestos, key="puesto_2")
        with col2:
            selected_seniority_2 = st.selectbox("Selecciona un Seniority (2)", seniorities, key="seniority_2")
        with col3:
            selected_locacion_2 = st.selectbox("Selecciona una Locación (2)", locaciones, key="locacion_2")

        df_selected_2 = df_tabla[
            (df_tabla['Puesto'] == selected_puesto_2) &
            (df_tabla['Seniority'] == selected_seniority_2) &
            (df_tabla['Locacion'] == selected_locacion_2]
        )

        if not df_selected_2.empty:
            st.markdown(f"**Valores Salariales para {selected_puesto_2} - {selected_seniority_2} - {selected_locacion_2}**")
            valores_2 = df_selected_2[['Q1', 'Q2', 'Q3', 'Q4', 'Q5']].iloc[0]
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("Q1, "Q", f"${valores_2:,.0f}")
            col2.metric("Q2", f"${valores_2['Q2']:,.0f}")
            col3.metric("Q3", f"${valores_2['Q3']:,.0f}")
            col4.metric("Q4", f"${valores_2['Q4']:,.0f}")
            col5.metric("Q5", f"${valores_2['Q5']:,.0f}")
        else:
            st.warning(f"No se encontraron datos para {selected_puesto_2} con Seniority {selected_seniority_2} en Locación {selected_locacion_2}.")
            valores_2 = None

        if valores_1 is not None and valores_2 is not None:
            st.markdown("### Comparativa de Sueldos")
            promedio_1 = valores_1[['Q1', 'Q2', 'Q3', 'Q4', 'Q5']].mean()
            promedio_2 = valores_2[['Q1', 'Q2', 'Q3', 'Q4', 'Q5']].mean()
            if promedio_1 != 0:
                porcentaje_diferencia = ((promedio_2 - promedio_1) / promedio_1) * 100
                st.markdown(f"**Diferencia porcentual (basada en el promedio de Q1-Q5):** {porcentaje_diferencia:.2f}%")
                if porcentaje_diferencia > 0:
                    st.write(f"El promedio de la segunda selección es {porcentaje_diferencia:.2f}% mayor que el de la primera.")
                elif porcentaje_diferencia < 0:
                    st.write(f"El promedio de la segunda selección es {abs(porcentaje_diferencia):.2f}% menor que el de la primera.")
                else:
                    st.write("No hay diferencia entre los promedios de ambas selecciones.")
            else:
                st.warning("No se puede calcular el porcentaje de diferencia porque el promedio de la primera selección es 0.")
        elif valores_1 is None or valores_2 is None:
            st.warning("No se puede calcular la diferencia porque una o ambas selecciones no tienen datos.")

        st.markdown("### Descargar Tabla Salarial Completa")
        col1, col2 = st.columns(2)
        with col1:
            csv = df_tabla.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Descargar tabla salarial completa como CSV",
                data=csv,
                file_name='tabla_salarial.csv',
                mime='text/csv',
            )
        with col2:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_tabla.to_excel(writer, index=False, sheet_name='Tabla Salarial')
            )
            excel_data = output.getvalue()
            st.download_button(
                label="Descargar tabla salarial completa como Excel",
                data=excel_data,
                file_name='tabla_salarial.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            )
```
