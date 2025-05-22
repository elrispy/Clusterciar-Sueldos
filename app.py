# --- Página: Reporte de Sueldos ---
if page == "Reporte de Sueldos":
    st.title("Reporte Interactivo de Sueldos")

    # Cargar el archivo Excel fijo (sin selección de dataset)
    @st.cache_data
    def load_data():
        return pd.read_excel("SUELDOS PARA INFORMES.xlsx", sheet_name=0)

    try:
        df = load_data()
    except FileNotFoundError:
        st.error("No se encontró el archivo SUELDOS PARA INFORMES.xlsx")
        st.stop()

    # Limpiar nombres de columnas
    df.columns = df.columns.str.strip().str.replace(' ', '_').str.replace('%_BANDA_SALARIAL', 'Porcentaje_Banda_Salarial')

    # Convertir columnas categóricas a string y manejar valores inválidos
    categorical_columns = [
        'Empresa', 'CCT', 'Grupo', 'Comitente', 'Puesto', 'seniority', 'Gerencia', 'CVH',
        'Puesto_tabla_salarial', 'Locacion', 'Centro_de_Costos', 'Especialidad', 'Superior',
        'Personaapellido', 'Personanombre'
    ]
    for col in categorical_columns:
        if col in df.columns:
            df[col] = df[col].astype(str).replace(['#Ref', 'nan'], '')

    # Convertir columnas de fecha (sin calcular Edad ni Antigüedad)
    date_columns = ['Fecha_de_Ingreso', 'Fecha_de_nacimiento']
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    # Normalizar Porcentaje_Banda_Salarial (asegurar que esté entre 0 y 1)
    if 'Porcentaje_Banda_Salarial' in df.columns:
        df['Porcentaje_Banda_Salarial'] = pd.to_numeric(df['Porcentaje_Banda_Salarial'], errors='coerce')
        df['Porcentaje_Banda_Salarial'] = df['Porcentaje_Banda_Salarial'].apply(lambda x: x / 100 if x > 1 else x)

    # Filtros en la barra lateral
    st.sidebar.header("Filtros")
    filtros = {}
    filter_columns = [
        'Empresa', 'CCT', 'Grupo', 'Comitente', 'Puesto', 'seniority', 'Gerencia', 'CVH',
        'Puesto_tabla_salarial', 'Locacion', 'Centro_de_Costos', 'Especialidad', 'Superior',
        'Personaapellido', 'Personanombre'
    ]
    for col in filter_columns:
        if col in df.columns:
            label = "Apellido" if col == "Personaapellido" else "Nombre" if col == "Personanombre" else col.replace('_', ' ').title()
            filtros[col] = st.sidebar.multiselect(label, df[col].unique())
        else:
            filtros[col] = []

    # Aplicar filtros
    df_filtered = df.copy()
    for key, values in filtros.items():
        if values:
            df_filtered = df_filtered[df_filtered[key].isin(values)]

    # Resumen General
    st.subheader("Resumen General - Sueldos para Informes")

    if len(df_filtered) > 0:
        # Calcular métricas (sin Edad ni Antigüedad)
        promedio_sueldo = df_filtered['Total_sueldo_bruto'].mean() if 'Total_sueldo_bruto' in df_filtered.columns else 0
        minimo_sueldo = df_filtered['Total_sueldo_bruto'].min() if 'Total_sueldo_bruto' in df_filtered.columns else 0
        maximo_sueldo = df_filtered['Total_sueldo_bruto'].max() if 'Total_sueldo_bruto' in df_filtered.columns else 0
        dispersion_sueldo = maximo_sueldo - minimo_sueldo
        dispersion_porcentaje = (dispersion_sueldo / minimo_sueldo * 100) if minimo_sueldo > 0 else 0
        costo_total = df_filtered['Costo_laboral'].sum() if 'Costo_laboral' in df_filtered.columns else 0

        # Distribución de Especialidad
        if 'Especialidad' in df_filtered.columns:
            especialidad_dist = df_filtered['Especialidad'].value_counts(normalize=True) * 100
            especialidad_dist = especialidad_dist.reset_index()
            especialidad_dist.columns = ['Especialidad', 'Porcentaje']
        else:
            especialidad_dist = pd.DataFrame()

        # Distribución de Bandas Salariales
        if 'Porcentaje_Banda_Salarial' in df_filtered.columns:
            banda_25 = len(df_filtered[df_filtered['Porcentaje_Banda_Salarial'] < 0.25]) / len(df_filtered) * 100
            banda_50 = len(df_filtered[df_filtered['Porcentaje_Banda_Salarial'] < 0.50]) / len(df_filtered) * 100
            banda_75 = len(df_filtered[df_filtered['Porcentaje_Banda_Salarial'] < 0.75]) / len(df_filtered) * 100
            banda_arriba_75 = len(df_filtered[df_filtered['Porcentaje_Banda_Salarial'] >= 0.75]) / len(df_filtered) * 100
        else:
            banda_25 = banda_50 = banda_75 = banda_arriba_75 = 0

        # Métricas en columnas (sin Edad ni Antigüedad)
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Personas", len(df_filtered))
        col2.metric("Sueldo Bruto Promedio", f"${promedio_sueldo:,.0f}")
        col3.metric("Sueldo Mínimo", f"${minimo_sueldo:,.0f}")
        col4.metric("Sueldo Máximo", f"${maximo_sueldo:,.0f}")

        col5, col6 = st.columns(2)
        col5.metric("Dispersión Salarial", f"${dispersion_sueldo:,.0f} ({dispersion_porcentaje:.1f}%)")
        col6.metric("Costo Laboral Total", f"${costo_total:,.0f}")

        # Distribución de Especialidad
        if 'Especialidad' in df_filtered.columns:
            st.markdown("### Distribución de Especialidad")
            especialidad_chart = alt.Chart(especialidad_dist).mark_bar().encode(
                x=alt.X('Porcentaje:Q', title='Porcentaje (%)'),
                y=alt.Y('Especialidad:N', title='Especialidad', sort='-x'),
                tooltip=['Especialidad', alt.Tooltip('Porcentaje:Q', format='.1f')]
            ).properties(height=300)
            st.altair_chart(especialidad_chart, use_container_width=True)

        # Distribución de Bandas Salariales
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

            # Mostrar porcentajes de bandas
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

    # Comparación por Categoría
    st.markdown("### Comparación por Categoría")
    agrupadores = [
        'Empresa', 'CCT', 'Grupo', 'Comitente', 'Puesto', 'seniority', 'Gerencia', 'CVH',
        'Puesto_tabla_salarial', 'Locacion', 'Centro_de_Costos', 'Especialidad', 'Superior'
    ]
    agrupadores = [col for col in agrupadores if col in df.columns]
    grupo_seleccionado = st.selectbox("Selecciona una categoría para agrupar", agrupadores, index=agrupadores.index('Puesto_tabla_salarial') if 'Puesto_tabla_salarial' in agrupadores else 0)

    if len(df_filtered) > 0:
        # Calcular métricas por grupo
        if 'Total_sueldo_bruto' in df_filtered.columns:
            grouped_data = df_filtered.groupby(grupo_seleccionado).agg({
                'Total_sueldo_bruto': ['mean', 'min', 'max'],
                'seniority': 'count'
            }).reset_index()
            grouped_data.columns = [grupo_seleccionado, 'Sueldo_Promedio', 'Sueldo_Mínimo', 'Sueldo_Máximo', 'Cantidad']
            grouped_data = grouped_data.dropna(subset=[grupo_seleccionado, 'Sueldo_Promedio'])
            grouped_data[grupo_seleccionado] = grouped_data[grupo_seleccionado].astype(str)

            # Gráfico de sueldos promedio
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

        # Si se selecciona Puesto_tabla_salarial, mostrar distribución de Seniority
        if grupo_seleccionado == 'Puesto_tabla_salarial' and 'Puesto_tabla_salarial' in df_filtered.columns and 'seniority' in df_filtered.columns:
            st.markdown("### Distribución de Seniority por Puesto Tabla Salarial")
            puestos_opciones = ['Todos los puestos'] + sorted(df_filtered['Puesto_tabla_salarial'].unique().tolist())
            puesto_seleccionado = st.selectbox("Selecciona un Puesto Tabla Salarial", puestos_opciones)
            
            # Filtro de Gerencia
            gerencias = sorted(df_filtered['Gerencia'].unique().tolist())
            gerencia_seleccionada = st.multiselect("Selecciona Gerencia(s)", gerencias, default=gerencias)

            # Filtrar datos según selección
            if puesto_seleccionado == 'Todos los puestos':
                df_puesto = df_filtered[df_filtered['Gerencia'].isin(gerencia_seleccionada)]
            else:
                df_puesto = df_filtered[
                    (df_filtered['Puesto_tabla_salarial'] == puesto_seleccionado) &
                    (df_filtered['Gerencia'].isin(gerencia_seleccionada))
                ]

            if len(df_puesto) > 0:
                # Calcular distribución de seniority
                seniority_dist = df_puesto['seniority'].value_counts(normalize=True) * 100
                seniority_dist = seniority_dist.reset_index()
                seniority_dist.columns = ['Seniority', 'Porcentaje']

                # Gráfico de distribución
                seniority_chart = alt.Chart(seniority_dist).mark_arc().encode(
                    theta=alt.Theta('Porcentaje:Q', stack=True),
                    color=alt.Color('Seniority:N', legend=alt.Legend(title="Seniority")),
                    tooltip=['Seniority', alt.Tooltip('Porcentaje:Q', format='.1f')]
                ).properties(width=300, height=300)
                st.altair_chart(seniority_chart, use_container_width=True)

                # Mostrar porcentajes de seniority
                st.markdown("**Porcentajes de Seniority**:")
                for _, row in seniority_dist.iterrows():
                    st.write(f"- {row['Seniority']}: {row['Porcentaje']:.1f}%")

                # Mostrar sueldos para el puesto seleccionado (si no es "Todos los puestos")
                if puesto_seleccionado != 'Todos los puestos' and 'Total_sueldo_bruto' in df_puesto.columns:
                    sueldo_stats = df_puesto['Total_sueldo_bruto'].agg(['min', 'mean', 'max']).round(0)
                    st.markdown(f"**Sueldos para {puesto_seleccionado} (filtrado por Gerencia)**:")
                    st.write(f"- Mínimo: ${sueldo_stats['min']:,.0f}")
                    st.write(f"- Promedio: ${sueldo_stats['mean']:,.0f}")
                    st.write(f"- Máximo: ${sueldo_stats['max']:,.0f}")
            else:
                st.warning("No hay datos para el puesto tabla salarial y gerencia seleccionados.")

        # Si se selecciona Seniority, mostrar sueldos
        if grupo_seleccionado == 'seniority' and 'seniority' in df_filtered.columns and 'Total_sueldo_bruto' in df_filtered.columns:
            sueldo_stats = grouped_data[['seniority', 'Sueldo_Mínimo', 'Sueldo_Promedio', 'Sueldo_Máximo']]
            st.markdown("**Sueldos por Seniority**:")
            st.dataframe(sueldo_stats)

    else:
        st.warning("No hay datos para mostrar en el gráfico de comparación por categoría.")

    # Tabla de datos filtrados
    st.subheader("Tabla de Datos Filtrados")
    st.dataframe(df_filtered)

    # Exportar a CSV
    csv = df_filtered.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Descargar datos filtrados como CSV",
        data=csv,
        file_name='sueldos_filtrados.csv',
        mime='text/csv',
    )

    # Exportar a Excel
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

    # Exportar a PDF
    if st.button("Generar reporte en PDF"):
        pdf = FPDF()
        pdf.add_page()

        # Usar Arial como fuente (PDF no soporta Red Hat Display directamente)
        pdf.set_font("Arial", size=12)

        # Agregar logo
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
                logo.save(tmpfile.name)
                pdf.image(tmpfile.name, x=10, y=8, w=50)
            os.unlink(tmpfile.name)
        except Exception as e:
            pdf.cell(200, 10, txt="Logo no disponible", ln=True, align='C')

        pdf.ln(30)
        # Limpiar texto para evitar caracteres no soportados
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

        # Agregar cuadro con datos si hay menos de 20 personas
        if len(df_filtered) < 20 and all(col in df_filtered.columns for col in ['Personaapellido', 'Personanombre', 'Puesto', 'Seniority', 'Porcentaje_Banda_Salarial', 'Total_sueldo_bruto']):
            pdf.ln(20)
            pdf.set_font("Arial", size=10)
            pdf.cell(200, 10, txt="Detalles de Personas (ordenado por Total Sueldo Bruto descendente)", ln=True, align='C')
            pdf.ln(5)

            # Crear tabla
            columns = ['Personaapellido', 'Personanombre', 'Puesto', 'Seniority', 'Porcentaje_Banda_Salarial', 'Total_sueldo_bruto']
            df_table = df_filtered[columns].sort_values(by='Total_sueldo_bruto', ascending=False)
            pdf.set_font("Arial", size=8)

            # Encabezados de la tabla
            for col in columns:
                pdf.cell(33, 10, clean_text(col.replace('_', ' ').title()), border=1, align='C')
            pdf.ln()

            # Datos de la tabla
            for index, row in df_table.iterrows():
                pdf.cell(33, 10, clean_text(str(row['Personaapellido'])), border=1)
                pdf.cell(33, 10, clean_text(str(row['Personanombre'])), border=1)
                pdf.cell(33, 10, clean_text(str(row['Puesto'])), border=1)
                pdf.cell(33, 10, clean_text(str(row['Seniority'])), border=1)
                pdf.cell(33, 10, clean_text(f"{row['Porcentaje_Banda_Salarial']*100:.1f}%"), border=1)
                pdf.cell(35, 10, clean_text(f"${row['Total_sueldo_bruto']:,.0f}"), border=1)
                pdf.ln()

        # Guardar PDF
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

    # Conclusión Final
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
        - Las especialidades más comunes son **{especialidad_dist.iloc[0]['Especialidad'] if not especialidad_dist.empty else 'N/A'}** ({especialidad_dist.iloc[0]['Porcentaje']:.1f}% si aplica).
        - **Recomendación**: Revisar los puestos con alta dispersión salarial y seniority bajo para ajustar políticas de compensación.
        """
        st.markdown(conclusion)
    else:
        st.markdown("No hay datos suficientes para generar una conclusión. Ajuste los filtros para incluir más datos.")
