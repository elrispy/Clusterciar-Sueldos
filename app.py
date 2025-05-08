import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from fpdf import FPDF
from datetime import datetime
from io import BytesIO

st.set_page_config(page_title="Reporte de Sueldos", layout="wide")
st.title("Reporte Interactivo de Sueldos")

# Cargar archivo Excel desde el proyecto
df = pd.read_excel("SUELDOS PARA INFORMES.xlsx", sheet_name=0)

st.sidebar.header("Filtros")
filtros = {
    "Empresa": st.sidebar.multiselect("Empresa", df["Empresa"].dropna().unique()),
    "CCT": st.sidebar.multiselect("CCT", df["CCT"].dropna().unique()),
    "Grupo": st.sidebar.multiselect("Grupo", df["Grupo"].dropna().unique()),
    "Comitente": st.sidebar.multiselect("Comitente", df["Comitente"].dropna().unique()),
    "Puesto": st.sidebar.multiselect("Puesto", df["Puesto"].dropna().unique()),
    "seniority": st.sidebar.multiselect("Seniority", df["seniority"].dropna().unique()),
    "Gerencia": st.sidebar.multiselect("Gerencia", df["Gerencia"].dropna().unique()),
    "CVH": st.sidebar.multiselect("CVH", df["CVH"].dropna().unique()),
    "Puesto tabla salarial": st.sidebar.multiselect("Puesto tabla salarial", df["Puesto tabla salarial"].dropna().unique()),
    "Locacion": st.sidebar.multiselect("Locacion", df["Locacion"].dropna().unique()),
}

df_filtered = df.copy()
for key, values in filtros.items():
    if values:
        df_filtered = df_filtered[df_filtered[key].isin(values)]

st.subheader("Resumen General")

# Cálculos clave
promedio = df_filtered['Total sueldo bruto'].mean()
minimo = df_filtered['Total sueldo bruto'].min()
maximo = df_filtered['Total sueldo bruto'].max()
mediana = df_filtered['Total sueldo bruto'].median()
costo_total = df_filtered['Total sueldo bruto'].sum() * 1.245

# Porcentaje del sueldo en la banda salarial (entre 25% y 75%)
if 'Sueldo mínimo' in df_filtered.columns and 'Sueldo máximo' in df_filtered.columns:
    df_filtered['% en banda'] = (df_filtered['Total sueldo bruto'] - df_filtered['Sueldo mínimo']) / (df_filtered['Sueldo máximo'] - df_filtered['Sueldo mínimo']) * 100
    en_banda = df_filtered[df_filtered['% en banda'].between(25, 75)]
    porcentaje_en_banda = len(en_banda) / len(df_filtered) * 100 if len(df_filtered) > 0 else 0
else:
    porcentaje_en_banda = np.nan

# Métricas visibles
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total personas", len(df_filtered))
col2.metric("Sueldo Bruto Promedio", f"${promedio:,.0f}")
col3.metric("Sueldo Mínimo / Máximo", f"${minimo:,.0f} / ${maximo:,.0f}")
col4.metric("Mediana Sueldo Bruto", f"${mediana:,.0f}")

col5, col6 = st.columns(2)
col5.metric("% empleados entre P25 y P75", f"{porcentaje_en_banda:.1f}%")
col6.metric("Costo Laboral Total (24.5%)", f"${costo_total:,.0f}")

# Interpretaciones automáticas
st.markdown("### Conclusiones")
conclusiones = []
if len(df_filtered) > 0:
    conclusiones.append(f"El sueldo bruto promedio es de ${promedio:,.0f}, con una mediana de ${mediana:,.0f}, lo que indica {'una distribución equilibrada' if abs(promedio - mediana) < 1000 else 'una posible asimetría en los datos'}.")
    conclusiones.append(f"El rango de sueldos va desde ${minimo:,.0f} hasta ${maximo:,.0f}.")
    if not np.isnan(porcentaje_en_banda):
        conclusiones.append(f"El {porcentaje_en_banda:.1f}% de las personas están dentro de la banda salarial entre el percentil 25 y 75, lo cual {'es adecuado' if porcentaje_en_banda > 50 else 'podría indicar desvíos salariales'}.")
    conclusiones.append(f"El costo laboral total estimado (sueldo + 24.5%) asciende a ${costo_total:,.0f}.")
    for c in conclusiones:
        st.markdown(f"- {c}")
else:
    st.info("No hay datos disponibles con los filtros actuales para generar conclusiones.")

# Generar PDF con FPDF
class PDF(FPDF):
    def header(self):
        self.image("07 (1).png", 10, 8, 40)
        self.set_font("Arial", 'B', 12)
        self.cell(0, 10, f"Clusterciar - Reporte de Sueldos ({datetime.today().strftime('%d/%m/%Y')})", ln=True, align="C")
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Página {self.page_no()}", align="C")

    def chapter_body(self, texto):
        self.set_font("Arial", "", 11)
        for linea in texto:
            self.multi_cell(0, 10, linea)
        self.ln()

# Botón para descargar PDF
if st.button("Descargar Informe en PDF"):
    pdf = PDF()
    pdf.add_page()
    pdf.chapter_body([f"Total de personas: {len(df_filtered)}",
                      f"Sueldo bruto promedio: ${promedio:,.0f}",
                      f"Sueldo mínimo: ${minimo:,.0f}",
                      f"Sueldo máximo: ${maximo:,.0f}",
                      f"Mediana: ${mediana:,.0f}",
                      f"% empleados en banda (P25-P75): {porcentaje_en_banda:.1f}%",
                      f"Costo laboral total: ${costo_total:,.0f}",
                      ""] + conclusiones)

    pdf_output = BytesIO()
    pdf.output(pdf_output)
    st.download_button(
        label="Descargar PDF",
        data=pdf_output.getvalue(),
        file_name="reporte_sueldos.pdf",
        mime="application/pdf"
    )

# Gráfico de distribución
st.markdown("### Distribución de Sueldos Brutos")
hist = alt.Chart(df_filtered).mark_bar(opacity=0.8).encode(
    alt.X("Total sueldo bruto", bin=alt.Bin(maxbins=40), title="Sueldo Bruto"),
    y='count()',
    tooltip=['count()']
).properties(height=300)
st.altair_chart(hist, use_container_width=True)

# Comparación por categoría
st.markdown("### Comparación por Categoría")
agrupadores = ["Empresa", "CCT", "Grupo", "Comitente", "Puesto", "seniority", "Gerencia", "CVH", "Puesto tabla salarial", "Locacion"]
grupo_seleccionado = st.selectbox("Selecciona una categoría para agrupar", agrupadores, index=6)

chart = alt.Chart(df_filtered).mark_bar().encode(
    x=alt.X(f"{grupo_seleccionado}:N", sort="-y"),
    y="mean(Total sueldo bruto):Q",
    tooltip=[grupo_seleccionado, "mean(Total sueldo bruto):Q"]
).properties(height=400)
st.altair_chart(chart, use_container_width=True)

st.subheader("Tabla de Datos Filtrados")
st.dataframe(df_filtered)

csv = df_filtered.to_csv(index=False).encode('utf-8')
st.download_button(
    label="Descargar datos filtrados como CSV",
    data=csv,
    file_name='sueldos_filtrados.csv',
    mime='text/csv',
)
