import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns

# Función para cargar datos con manejo de diferentes delimitadores
def cargar_datos():
    archivos = {
        '2023': '202312-informe-ministerio-actualizado-dic.csv',
        'aeropuertos': 'aeropuertos_detalle.csv',
        '2019': '2019_informe_ministerio.csv',
        '2020': '2020_informe_ministerio.csv',
        '2022': '202212-informe-ministerio.csv',
        '2024': '202404-informe-ministerio.csv',
        '2021': '202112_informe_ministerio.csv'
    }
    base_path = 'dataset/'
    datos = {}
    for key, filename in archivos.items():
        full_path = base_path + filename
        try:
            datos[key] = pd.read_csv(full_path, delimiter=';')
        except Exception as e:
            st.error(f"Error al cargar {filename}: {str(e)}")
            datos[key] = pd.DataFrame()  # Usa un DataFrame vacío en caso de error
    return datos

datos = cargar_datos()

# Uniformizar las columnas de los DataFrames
def uniformizar_columnas(df):
    df = df.rename(columns=lambda x: x.strip())  # Eliminar espacios en blanco alrededor de los nombres de columnas
    if 'Fecha UTC' in df.columns:
        df = df.rename(columns={'Fecha UTC': 'Fecha'})
    if 'Pasajeros' not in df.columns and 'PAX' in df.columns:
        df = df.rename(columns={'PAX': 'Pasajeros'})
    return df

# Aplicar la uniformización a todos los DataFrames
for key in datos:
    datos[key] = uniformizar_columnas(datos[key])

# Preprocesamiento y combinación de datos de vuelos
def combinar_datos_vuelos():
    # Combina todos los DataFrames relevantes
    dfs = []
    for key in ['2019', '2020', '2022', '2024', '2023', '2021']:
        if key in datos:
            df = datos[key]
            # Asegurarse de que la columna de fecha esté presente y correctamente formateada
            if 'Fecha' in df.columns:
                df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce')
            dfs.append(df)
    df_combined = pd.concat(dfs, ignore_index=True)
    return df_combined

df_combined = combinar_datos_vuelos()

# Sidebar para opciones de visualización
st.sidebar.title("Análisis de Datos de Aeropuertos")
analysis_type = st.sidebar.selectbox(
    "Seleccione el tipo de análisis:",
    ['Vuelos Diarios', 'Actividad de Aeropuertos', 'Tipo de Aviones', 'Comparativa Anual', 'Detalles del Aeropuerto', 'Resumen de Datos']
)

# Funciones para visualización de datos
def vuelos_diarios():
    st.title("Vuelos Diarios")
    # Ajuste del nombre de la columna de fecha
    fecha_columna = 'Fecha'

    if fecha_columna:
        # Selección de rango de fechas
        min_date = df_combined[fecha_columna].min()
        max_date = df_combined[fecha_columna].max()
        start_date, end_date = st.date_input("Seleccione el rango de fechas:", [min_date, max_date], min_value=min_date, max_value=max_date)

        if start_date and end_date:
            df_filtered = df_combined[(df_combined[fecha_columna] >= pd.to_datetime(start_date)) & (df_combined[fecha_columna] <= pd.to_datetime(end_date))]
        
            if not df_filtered.empty:
                # Gráfico de líneas para vuelos diarios
                fig_line = px.line(df_filtered, x=fecha_columna, y='Pasajeros', title='Vuelos Diarios')
                st.plotly_chart(fig_line)

                # Mostrar uno a uno los gráficos con botones
                if st.button('Mostrar Histograma'):
                    fig_hist = px.histogram(df_filtered, x=fecha_columna, y='Pasajeros', nbins=30, title='Distribución de Vuelos Diarios')
                    st.plotly_chart(fig_hist)

                if st.button('Mostrar Gráfico de Barras por Mes'):
                    df_filtered['Mes'] = df_filtered[fecha_columna].dt.month
                    df_monthly = df_filtered.groupby('Mes')['Pasajeros'].sum().reset_index()
                    fig_bar = px.bar(df_monthly, x='Mes', y='Pasajeros', title='Vuelos Diarios por Mes')
                    st.plotly_chart(fig_bar)

                if st.button('Mostrar Gráfico de Dispersión'):
                    fig_scatter = px.scatter(df_filtered, x=fecha_columna, y='Pasajeros', title='Dispersión de Vuelos Diarios')
                    st.plotly_chart(fig_scatter)
            else:
                st.write("No hay datos disponibles para el rango de fechas seleccionado.")
    else:
        st.error("No se encontró una columna de fecha adecuada.")

def actividad_aeropuertos():
    st.title("Actividad de Aeropuertos")
    df_aggregated = df_combined.groupby('Aeropuerto').size().reset_index(name='cantidad_vuelos')
    fig = px.bar(df_aggregated, x='Aeropuerto', y='cantidad_vuelos', title='Actividad por Aeropuerto')
    st.plotly_chart(fig)

def tipo_aviones():
    st.title("Tipo de Aviones")
    fig = px.pie(df_combined, names='Aeronave', title='Distribución de Tipos de Avión')
    st.plotly_chart(fig)

def comparativa_anual():
    st.title("Comparativa Anual de Vuelos")
    fecha_columna = 'Fecha'

    if fecha_columna:
        df_combined['año'] = df_combined[fecha_columna].dt.year
        # Asegurarse de sumar solo las columnas numéricas
        df_aggregated = df_combined.groupby('año').sum(numeric_only=True).reset_index()
        fig = px.bar(df_aggregated, x='año', y='Pasajeros', title='Comparativa Anual de Vuelos')
        st.plotly_chart(fig)
    else:
        st.error("No se encontró una columna de fecha adecuada.")

def detalles_aeropuerto():
    st.title("Detalles del Aeropuerto Seleccionado")
    if datos['aeropuertos'].empty:
        st.error("Datos de aeropuertos no disponibles.")
    else:
        selected_airport = st.selectbox("Elija un aeropuerto", datos['aeropuertos']['denominacion'])
        st.write(f"Aeropuerto seleccionado: {selected_airport}")
        st.write(datos['aeropuertos'][datos['aeropuertos']['denominacion'] == selected_airport])
        airport_code = datos['aeropuertos'][datos['aeropuertos']['denominacion'] == selected_airport]['local'].values[0]
        st.write(f"Código del aeropuerto: {airport_code}")
        

def resumen_datos():
    st.title("Resumen de Datos")
    st.write(f"Total de registros: {len(df_combined)}")
    st.write(f"Total de columnas: {len(df_combined.columns)}")
    st.write("Resumen de datos por archivo:")
    for key, df in datos.items():
        st.write(f"{key}: {len(df)} registros")

# Ejecución de la funcionalidad basada en la selección del usuario
if analysis_type == 'Vuelos Diarios':
    vuelos_diarios()
elif analysis_type == 'Actividad de Aeropuertos':
    actividad_aeropuertos()
elif analysis_type == 'Tipo de Aviones':
    tipo_aviones()
elif analysis_type == 'Comparativa Anual':
    comparativa_anual()
elif analysis_type == 'Detalles del Aeropuerto':
    detalles_aeropuerto()
elif analysis_type == 'Resumen de Datos':
    resumen_datos()
