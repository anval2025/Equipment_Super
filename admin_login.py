import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="CONTROL DE EQUIPO", layout="wide")
DB_PATH = "data/plantlist.db"

# --- CONEXIÓN A DB ---
def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

# --- LOGIN SIMPLE ---
def login():
    st.title("🔐 Inicio de Sesión")
    user = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")
    if st.button("Iniciar sesión"):
        if user == "admin" and password == "1234567890":
            st.session_state["logged_in"] = True
            st.session_state["usuario"] = user
            st.success("✅ Inicio de sesión exitoso.")
        else:
            st.error("Usuario o contraseña incorrectos ❌")

# --- FUNCION DISPONIBILIDAD ---
def mostrar_disponibilidad(df_equipos, tipo_equipo, titulo):
    st.subheader(f"Disponibilidad de {titulo} por LOCATION")
    df_gruas = df_equipos[df_equipos["TIPO_EQUIPO"] == tipo_equipo]

    if df_gruas.empty:
        st.info("No hay grúas de este tipo.")
    else:
        locations = df_gruas["LOCATION"].unique()
        for i, loc in enumerate(locations):
            st.markdown(f"### Ubicación: {loc}")
            df_loc = df_gruas[df_gruas["LOCATION"] == loc]

            conteo_status = df_loc["STATUS"].value_counts().reindex(["DISPONIBLE","NO DISPONIBLE"], fill_value=0)
            total = conteo_status.sum()
            disponibles = conteo_status.get("DISPONIBLE", 0)
            texto_central = f"{disponibles} / {total}"
            font_size = 20

            fig = go.Figure(data=[go.Pie(
                labels=conteo_status.index,
                values=conteo_status.values,
                hole=0.5,
                marker_colors=["#5DADE2", "#D3D3D3"],
                textinfo='percent',
                insidetextorientation='radial',
                insidetextfont=dict(size=font_size, color="black")
            )])
            fig.update_layout(
                annotations=[dict(text=texto_central, x=0.5, y=0.5, font_size=font_size, font_color="black", showarrow=False)],
                showlegend=True
            )
            st.plotly_chart(fig, use_container_width=True, key=f"{tipo_equipo}_{loc}_{i}")

            with st.expander(f"Lista de grúas en {loc}"):
                df_loc_display = df_loc[["EQUIPO", "STATUS", "OBSERVACIONES"]].copy()
                df_loc_display.insert(0, "No.", range(1, len(df_loc_display) + 1))
                st.data_editor(df_loc_display, use_container_width=True, hide_index=True)

# --- APP ADMIN ---
def app_admin():
    conn = get_connection()
    df_equipos = pd.read_sql_query("SELECT * FROM equipos", conn)
    df_historial = pd.read_sql_query("SELECT * FROM cambios_status", conn)

    st.sidebar.title("📂 Menú")

    if "vista" not in st.session_state:
        st.session_state["vista"] = "tabla"

    # Botones menú lateral
    if st.sidebar.button("✏️ Equipos"): st.session_state["vista"] = "tabla"
    if st.sidebar.button("📊 Disponibilidad QC"): st.session_state["vista"] = "disponibilidad_gp"
    if st.sidebar.button("📊 Disponibilidad RS"): st.session_state["vista"] = "disponibilidad_rs"
    if st.sidebar.button("📊 Disponibilidad RTG"): st.session_state["vista"] = "disponibilidad_rtg"
    if st.sidebar.button("📊 Disponibilidad EH"): st.session_state["vista"] = "disponibilidad_eh"
    if st.sidebar.button("📜 Historial"): st.session_state["vista"] = "historial"

    # --- VISTAS ---
    if st.session_state["vista"] == "disponibilidad_rs":
        mostrar_disponibilidad(df_equipos, "GRUA MOVIL MANIPULADOR PARA LLENOS", "GRUA MOVIL MANIPULADOR PARA LLENOS")
    elif st.session_state["vista"] == "disponibilidad_rtg":
        mostrar_disponibilidad(df_equipos, "GRUA DE MARCO", "GRUA DE MARCO")
    elif st.session_state["vista"] == "disponibilidad_gp":
        mostrar_disponibilidad(df_equipos, "GRUA PORTICO", "GRUA PORTICO")
    elif st.session_state["vista"] == "disponibilidad_eh":
        mostrar_disponibilidad(df_equipos, "GRUA MOVIL MANIPULADOR PARA VACIOS", "GRUA MOVIL MANIPULADOR PARA VACIOS")
    elif st.session_state["vista"] == "historial":
        st.subheader("Historial de cambios de STATUS")
        df_historial = pd.read_sql_query("SELECT * FROM cambios_status", conn)

        filtro = st.text_input("🔍 Buscar en todas las columnas")
        df_filtrado = df_historial.copy()
        if filtro:
            mask = pd.Series(False, index=df_filtrado.index)
            for col in df_filtrado.columns:
                mask = mask | df_filtrado[col].astype(str).str.contains(filtro, case=False, na=False)
            df_filtrado = df_filtrado[mask]

        st.data_editor(df_filtrado, use_container_width=True, hide_index=False)

    elif st.session_state["vista"] == "tabla":
        st.write("### 🧾 Tabla de equipos (editable, solo ID no editable)")
        search_text = st.text_input("🔍 Buscar en todas las columnas")
        df_filtered = df_equipos.copy()
        if search_text:
            mask = pd.Series(False, index=df_filtered.index)
            for col in df_filtered.columns:
                mask = mask | df_filtered[col].astype(str).str.contains(search_text, case=False, na=False)
            df_filtered = df_filtered[mask]

        # --- Configuración de columnas ---
        column_config_dict = {}
        for col in df_filtered.columns:
            if col == "ID":
                column_config_dict[col] = st.column_config.TextColumn(col, disabled=True)
            elif col == "STATUS":
                # Checkbox toggle para STATUS
                df_filtered["STATUS"] = df_filtered["STATUS"].apply(lambda x: True if x=="DISPONIBLE" else False)
                column_config_dict[col] = st.column_config.CheckboxColumn(
                    "Disponible",
                    help="Marcado → DISPONIBLE, No marcado → NO DISPONIBLE",
                    width=120
                )

        # Mostrar tabla editable
        edited_df = st.data_editor(
            df_filtered,
            column_config=column_config_dict,
            use_container_width=True,
            hide_index=True
        )

        # Convertimos checkbox a DISPONIBLE/NO DISPONIBLE
        edited_df["STATUS"] = edited_df["STATUS"].apply(lambda x: "DISPONIBLE" if x else "NO DISPONIBLE")

        if st.button("💾 Guardar cambios"):
            cambios_realizados = 0
            for idx, row_new in edited_df.iterrows():
                equipo_id = row_new["ID"]
                row_old = df_equipos[df_equipos["ID"] == equipo_id].iloc[0]

                # Guardar cambios de otras columnas
                update_cols = []
                update_vals = []
                for col in df_equipos.columns:
                    if col != "ID" and col != "STATUS" and str(row_new[col]) != str(row_old[col]):
                        update_cols.append(f"{col} = ?")
                        update_vals.append(row_new[col])
                if update_cols:
                    update_vals.append(equipo_id)
                    conn.execute(f"UPDATE equipos SET {', '.join(update_cols)} WHERE ID = ?", update_vals)

                # Guardar cambios de STATUS
                old_status = str(row_old["STATUS"]).strip().upper()
                new_status = str(row_new["STATUS"]).strip().upper()
                if old_status != new_status:
                    columnas_status = ["TIPO_EQUIPO","EQUIPO","STATUS","LOCATION","OBSERVACIONES","PROPIETARIO","ARRENDAMIENTO"]
                    valores_status = [str(row_new.get(col, "")) for col in columnas_status]
                    valores_status.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    conn.execute(f"""
                        INSERT INTO cambios_status ({", ".join(columnas_status)}, FECHA_CAMBIO)
                        VALUES ({", ".join(["?"]*len(valores_status))})
                    """, valores_status)
                    # Actualizar en tabla principal
                    conn.execute("UPDATE equipos SET STATUS = ? WHERE ID = ?", (new_status, equipo_id))
                    cambios_realizados += 1

            conn.commit()
            conn.close()
            st.success(f"✅ Se actualizaron {cambios_realizados} filas con cambios de STATUS y todos los demás cambios se guardaron.")

# --- MAIN ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if st.session_state["logged_in"]:
    app_admin()
else:
    login()
