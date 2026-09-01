# =========================================================
# ARCHIVO: champions.py
# VERSIÓN: v.1.9.3 (Champions Mandinguera - Vista Móvil / Compacta)
# =========================================================

import base64
import json
import re
from pathlib import Path
import requests
import streamlit as st

# ---------------------------------------------------------
# 1. ARCHIVOS Y RUTAS BASE
# ---------------------------------------------------------
BASE_DIR = Path(__file__).parent
ASSETS_DIR = BASE_DIR / "assets"
LOGO_PATH = ASSETS_DIR / "Champions.png"
ESCUDOS_DIR = ASSETS_DIR / "escudos"

# Diccionario de abreviaturas oficiales (13 equipos)
ABREVIATURAS = {
    "Maccabi de Levantá": "MCL",
    "Bass-T-Nation United": "BTN",
    "Rayo Malayo": "RAY",
    "LA MERIDA GUSTO FC": "LMG",
    "Al-larik-apapa": "ALP",
    "Estrella Galicia CF": "ESG",
    "La casa de la Juventus": "JUV",
    "AC Poniente": "ACP",
    "Apoel Barceló C.F.": "APO",
    "Olympique de Mamársella": "OLM",
    "Emerita Adisgusta!": "EMD",
    "Wine & Horses": "W&H",
    "Cskalaropa": "CSK"
}

EQUIVALENCIAS_NOMBRES = {
    "CSKAlaropa": "Cskalaropa"
}

# Distribución de los 13 equipos en 3 grupos
GRUPOS_EQUIPOS = {
    "GRUPO A": [
        "Maccabi de Levantá",
        "Bass-T-Nation United",
        "Rayo Malayo",
        "LA MERIDA GUSTO FC"
    ],
    "GRUPO B": [
        "Al-larik-apapa",
        "Estrella Galicia CF",
        "La casa de la Juventus",
        "AC Poniente"
    ],
    "GRUPO C": [
        "Apoel Barceló C.F.",
        "Olympique de Mamársella",
        "Emerita Adisgusta!",
        "Wine & Horses",
        "Cskalaropa"
    ]
}

EQUIPOS_TOTALES = set(ABREVIATURAS.keys())

def normalizar_nombre_equipo(nombre):
    """Traduce el nombre del calendario al nombre oficial de la API si existe equivalencia."""
    return EQUIVALENCIAS_NOMBRES.get(nombre, nombre)


def obtener_grupo_equipo(nombre_equipo):
    """Devuelve el grupo al que pertenece un equipo."""
    norm_eq = normalizar_nombre_equipo(nombre_equipo)
    for grupo, equipos_lista in GRUPOS_EQUIPOS.items():
        for eq in equipos_lista:
            if normalizar_nombre_equipo(eq).lower() == norm_eq.lower():
                return grupo
    return ""


# ---------------------------------------------------------
# MAPEO DE JORNADAS CHAMPIONS CON LA LIGA REAL
# ---------------------------------------------------------
MAPEO_LIGA_REAL = {
    1: 5,
    2: 9,
    3: 10,
    4: 12,
    5: 14,
    6: 16
}


# ---------------------------------------------------------
# CALENDARIO OFICIAL FASE DE LIGA (100% INTRA-GRUPO)
# ---------------------------------------------------------
CALENDARIO_JORNADAS = {
    1: [
        # Grupo A
        ("Rayo Malayo", "Bass-T-Nation United"),
        ("LA MERIDA GUSTO FC", "Maccabi de Levantá"),
        # Grupo B
        ("Al-larik-apapa", "Estrella Galicia CF"),
        ("La casa de la Juventus", "AC Poniente"),
        # Grupo C
        ("Apoel Barceló C.F.", "Olympique de Mamársella"),
        ("Emerita Adisgusta!", "Wine & Horses")
        # Descansa Cskalaropa en Grupo C
    ],
    2: [
        # Grupo A
        ("Maccabi de Levantá", "Rayo Malayo"),
        ("Bass-T-Nation United", "LA MERIDA GUSTO FC"),
        # Grupo B
        ("AC Poniente", "Al-larik-apapa"),
        ("Estrella Galicia CF", "La casa de la Juventus"),
        # Grupo C
        ("Wine & Horses", "Apoel Barceló C.F."),
        ("Cskalaropa", "Emerita Adisgusta!")
        # Descansa Olympique de Mamársella en Grupo C
    ],
    3: [
        # Grupo A
        ("Rayo Malayo", "LA MERIDA GUSTO FC"),
        ("Maccabi de Levantá", "Bass-T-Nation United"),
        # Grupo B
        ("Al-larik-apapa", "La casa de la Juventus"),
        ("Estrella Galicia CF", "AC Poniente"),
        # Grupo C
        ("Apoel Barceló C.F.", "Cskalaropa"),
        ("Olympique de Mamársella", "Wine & Horses")
        # Descansa Emerita Adisgusta! en Grupo C
    ],
    4: [
        # Grupo A (Segunda vuelta / cruces internos)
        ("Bass-T-Nation United", "Rayo Malayo"),
        ("Maccabi de Levantá", "LA MERIDA GUSTO FC"),
        # Grupo B
        ("Estrella Galicia CF", "Al-larik-apapa"),
        ("AC Poniente", "La casa de la Juventus"),
        # Grupo C
        ("Olympique de Mamársella", "Apoel Barceló C.F."),
        ("Wine & Horses", "Emerita Adisgusta!")
        # Descansa Cskalaropa en Grupo C
    ],
    5: [
        # Grupo A
        ("Rayo Malayo", "Maccabi de Levantá"),
        ("LA MERIDA GUSTO FC", "Bass-T-Nation United"),
        # Grupo B
        ("Al-larik-apapa", "AC Poniente"),
        ("La casa de la Juventus", "Estrella Galicia CF"),
        # Grupo C
        ("Apoel Barceló C.F.", "Wine & Horses"),
        ("Emerita Adisgusta!", "Cskalaropa")
        # Descansa Olympique de Mamársella en Grupo C
    ],
    6: [
        # Grupo A
        ("LA MERIDA GUSTO FC", "Rayo Malayo"),
        ("Bass-T-Nation United", "Maccabi de Levantá"),
        # Grupo B
        ("La casa de la Juventus", "Al-larik-apapa"),
        ("AC Poniente", "Estrella Galicia CF")
        # Grupo C: Se calcula dinámicamente (1º vs 4º y 2º vs 3º)
    ]
}


def get_image_base64(path_str_or_path):
    """Convierte una ruta local a cadena Base64 para HTML."""
    if not path_str_or_path:
        return None
    p = Path(path_str_or_path)
    if p.exists() and p.is_file():
        with open(p, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    return None


def obtener_ruta_escudo(team_id, escudo_url_api=None):
    """Busca primero el escudo localmente y si no, usa la URL de la API."""
    if ESCUDOS_DIR.exists() and team_id:
        for ext in [".png", ".jpg", ".jpeg", ".webp", ".svg"]:
            escudo_local = ESCUDOS_DIR / f"{team_id}{ext}"
            if escudo_local.exists():
                return str(escudo_local)
    return escudo_url_api


def buscar_equipo_info(nombre_calendario, equipos_dict):
    """Busca de forma flexible la información de un equipo."""
    if not equipos_dict:
        return {}
    nombre_busq = normalizar_nombre_equipo(nombre_calendario)
    if nombre_busq in equipos_dict:
        return equipos_dict[nombre_busq]
    for k, v in equipos_dict.items():
        if k.lower() == nombre_busq.lower():
            return v
    def normalizar(s):
        return re.sub(r'[^a-zA-Z0-9]', '', s).lower()
    norm_buscado = normalizar(nombre_busq)
    for k, v in equipos_dict.items():
        if normalizar(k) == norm_buscado:
            return v
    return {}


# ---------------------------------------------------------
# REGLA OFICIAL DE CONVERSIÓN DE PUNTOS A GOLES
# ---------------------------------------------------------
def puntos_a_goles_base(pts):
    if pts <= 49: return 0
    elif 50 <= pts <= 69: return 1
    elif 70 <= pts <= 79: return 2
    elif 80 <= pts <= 89: return 3
    elif 90 <= pts <= 99: return 4
    elif 100 <= pts <= 109: return 5
    else: return 5 + (pts - 100) // 10


def calcular_goles_partido(pts1, pts2, aplicar_regla_diferencia=True):
    g1 = puntos_a_goles_base(pts1)
    g2 = puntos_a_goles_base(pts2)
    if aplicar_regla_diferencia and g1 == g2:
        if pts1 > pts2 and (pts1 - pts2) >= 10:
            g1 += 1
        elif pts2 > pts1 and (pts2 - pts1) >= 10:
            g2 += 1
    return g1, g2


# ---------------------------------------------------------
# 2. FUNCIONES API FUTMONDO & CACHÉ (Robustas contra bools/None)
# ---------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def login_futmondo(email, password):
    url_login = "https://api.futmondo.com/5/login/with_mail"
    payload = {
        "header": {"token": "null", "userid": ""},
        "query": {"mail": email, "pwd": password},
        "answer": {},
    }
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(url_login, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        answer = data.get("answer")
        if isinstance(answer, dict):
            mobile_data = answer.get("mobile", {})
            if isinstance(mobile_data, dict):
                return mobile_data.get("token"), mobile_data.get("userid")
        return None, None
    except Exception:
        return None, None


@st.cache_data(ttl=600, show_spinner=False)
def obtener_equipos_liga(token, userid, championship_id):
    url = "https://api.futmondo.com/2/championship/teams"
    payload = {
        "header": {"token": token, "userid": userid},
        "query": {"championshipId": championship_id},
        "answer": {},
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        answer = data.get("answer")
        teams_list = []
        if isinstance(answer, dict):
            teams_list = answer.get("teams", [])
        if not isinstance(teams_list, list):
            teams_list = []

        equipos_map = {}
        for team in teams_list:
            if isinstance(team, dict):
                team_id = team.get("id") or team.get("teamid")
                nombre = team.get("teamname")
                if nombre:
                    equipos_map[nombre] = {
                        "id": team_id,
                        "nombre_equipo": nombre,
                        "escudo_url": team.get("photo"),
                    }
        return equipos_map
    except Exception:
        return {}


@st.cache_data(ttl=600, show_spinner=False)
def obtener_jornadas_usuario(token, userid, championship_id, userteam_id):
    url = "https://api.futmondo.com/1/userteam/rounds"
    payload = {
        "header": {"token": token, "userid": userid},
        "query": {"championshipId": championship_id, "userteamId": userteam_id},
        "answer": {}
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        answer = data.get("answer")
        if isinstance(answer, list):
            return answer
        return []
    except Exception:
        return []


@st.cache_data(ttl=600, show_spinner=False)
def obtener_ranking_jornada(token, userid, championship_id, userteam_id, round_id):
    url = "https://api.futmondo.com/1/ranking/round"
    payload = {
        "header": {"token": token, "userid": userid},
        "query": {
            "championshipId": championship_id,
            "roundNumber": round_id,
            "userteamId": userteam_id
        },
        "answer": {}
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        answer = data.get("answer")
        if isinstance(answer, dict):
            ranking = answer.get("ranking")
            if isinstance(ranking, list):
                return ranking
        return []
    except Exception:
        return []


# ---------------------------------------------------------
# 3. CÁLCULO DE CLASIFICACIÓN POR GRUPOS Y MEJORES TERCEROS
# ---------------------------------------------------------
def calcular_clasificacion_grupos(equipos_map, rounds_info, token, userid, championship_id, userteam_id, hasta_jornada=6):
    stats = {}
    for nombre_eq in equipos_map.keys():
        stats[nombre_eq] = {
            "Equipo": nombre_eq,
            "id": equipos_map[nombre_eq]["id"],
            "escudo": obtener_ruta_escudo(equipos_map[nombre_eq]["id"], equipos_map[nombre_eq].get("escudo_url")),
            "J": 0, "G": 0, "E": 0, "P": 0, "GF": 0, "GC": 0, "DG": 0, "Puntos": 0, "SUM": 0
        }

    if not isinstance(rounds_info, list):
        rounds_info = []

    jornadas_cerradas = [r for r in rounds_info if isinstance(r, dict) and r.get("status") == "closed"]
    jornadas_cerradas = sorted(jornadas_cerradas, key=lambda x: x.get("number", 0))

    for r in jornadas_cerradas:
        num_jornada = r.get("number")
        if num_jornada > hasta_jornada:
            continue
        round_id = r.get("id")
        ranking_data = obtener_ranking_jornada(token, userid, championship_id, userteam_id, round_id)
        
        puntos_fantasy = {}
        for item in ranking_data:
            if isinstance(item, dict):
                nombre_api = item.get("name")
                pts = item.get("points", 0)
                info_eq = buscar_equipo_info(nombre_api, equipos_map)
                if info_eq and "nombre_equipo" in info_eq:
                    puntos_fantasy[info_eq["nombre_equipo"]] = pts

        partidos = obtener_partidos_jornada_evaluados(num_jornada, equipos_map, rounds_info, token, userid, championship_id, userteam_id)
        for eq1_cal, eq2_cal in partidos:
            eq1 = normalizar_nombre_equipo(eq1_cal)
            eq2 = normalizar_nombre_equipo(eq2_cal)

            if eq1 in stats and eq2 in stats:
                pts1 = puntos_fantasy.get(eq1, 0)
                pts2 = puntos_fantasy.get(eq2, 0)

                stats[eq1]["SUM"] += pts1
                stats[eq2]["SUM"] += pts2

                gf1, gf2 = calcular_goles_partido(pts1, pts2, aplicar_regla_diferencia=True)

                if gf1 > gf2: res1, res2 = "G", "P"
                elif gf1 < gf2: res1, res2 = "P", "G"
                else: res1, res2 = "E", "E"

                stats[eq1]["J"] += 1; stats[eq1]["GF"] += gf1; stats[eq1]["GC"] += gf2
                if res1 == "G": stats[eq1]["G"] += 1; stats[eq1]["Puntos"] += 3
                elif res1 == "E": stats[eq1]["E"] += 1; stats[eq1]["Puntos"] += 1
                else: stats[eq1]["P"] += 1

                stats[eq2]["J"] += 1; stats[eq2]["GF"] += gf2; stats[eq2]["GC"] += gf1
                if res2 == "G": stats[eq2]["G"] += 1; stats[eq2]["Puntos"] += 3
                elif res2 == "E": stats[eq2]["E"] += 1; stats[eq2]["Puntos"] += 1
                else: stats[eq2]["P"] += 1

    # Organizar por grupos
    clasificaciones_grupos = {}
    for nombre_grupo, lista_nombres_eqs in GRUPOS_EQUIPOS.items():
        grupo_stats = []
        for eq_nombre in lista_nombres_eqs:
            matched_key = None
            for k in stats.keys():
                if k.lower() == eq_nombre.lower():
                    matched_key = k
                    break
            if matched_key and matched_key in stats:
                grupo_stats.append(stats[matched_key])
            else:
                grupo_stats.append({
                    "Equipo": eq_nombre,
                    "id": None,
                    "escudo": None,
                    "J": 0, "G": 0, "E": 0, "P": 0, "GF": 0, "GC": 0, "DG": 0, "Puntos": 0, "SUM": 0
                })

        grupo_stats = sorted(grupo_stats, key=lambda x: (x["Puntos"], x["DG"], x["GF"], x["SUM"]), reverse=True)
        for idx, row in enumerate(grupo_stats):
            row["Pos"] = idx + 1
        clasificaciones_grupos[nombre_grupo] = grupo_stats

    # Identificar los dos mejores terceros entre todos los grupos
    terceros = []
    for nombre_grupo, grupo_stats in clasificaciones_grupos.items():
        if len(grupo_stats) >= 3:
            terceros.append(grupo_stats[2])
    
    terceros_ordenados = sorted(
        terceros, 
        key=lambda x: (x["Puntos"], x["DG"], x["GF"], x["SUM"]), 
        reverse=True
    )
    mejores_terceros_nombres = {t["Equipo"] for t in terceros_ordenados[:2]}

    for nombre_grupo, grupo_stats in clasificaciones_grupos.items():
        for row in grupo_stats:
            if row["Pos"] == 3 and row["Equipo"] in mejores_terceros_nombres:
                row["es_mejor_tercero"] = True
            else:
                row["es_mejor_tercero"] = False

    return clasificaciones_grupos


def obtener_partidos_jornada_evaluados(num_jornada, equipos_map, rounds_info, token, userid, championship_id, userteam_id):
    """Devuelve los partidos de una jornada, calculando dinámicamente el Grupo C en la jornada 6."""
    partidos_base = CALENDARIO_JORNADAS.get(num_jornada, [])
    
    # Si no es la jornada 6, devolvemos los partidos base estáticos (todos intra-grupo)
    if num_jornada != 6 or not equipos_map or not rounds_info or not token or not userid:
        return partidos_base

    # Para la jornada 6, calculamos la clasificación hasta la jornada 5 para el Grupo C
    clasificacion_hasta_5 = calcular_clasificacion_grupos(equipos_map, rounds_info, token, userid, championship_id, userteam_id, hasta_jornada=5)
    grupo_c_stats = clasificacion_hasta_5.get("GRUPO C", [])

    partidos_j6_c = []
    if len(grupo_c_stats) >= 4:
        eq_1 = grupo_c_stats[0]["Equipo"]
        eq_2 = grupo_c_stats[1]["Equipo"]
        eq_3 = grupo_c_stats[2]["Equipo"]
        eq_4 = grupo_c_stats[3]["Equipo"]
        
        # 1º vs 4º y 2º vs 3º
        partidos_j6_c.append((eq_1, eq_4))
        partidos_j6_c.append((eq_2, eq_3))

    partidos_ab = [p for p in partidos_base if obtener_grupo_equipo(p[0]) in ["GRUPO A", "GRUPO B"]]
    return partidos_ab + partidos_j6_c


# ---------------------------------------------------------
# 4. RENDERIZADOR DE TABLA DE GRUPO (SOPORTE MÓVIL / COMPACTO)
# ---------------------------------------------------------
def render_tabla_grupo(datos_grupo, titulo_grupo, modo_movil=False):
    css_style = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@600;700;800;900&display=swap');
.excel-table-container { width: 100%; overflow-x: auto; margin-top: -3px; background: #0b1a40; border-radius: 8px; padding: 8px; border: 1px solid rgba(0, 163, 224, 0.3) !important; box-sizing: border-box; margin-bottom: 20px; }
.excel-table { width: 100%; border-collapse: collapse; font-family: 'Montserrat', sans-serif; color: #ffffff; font-size: 0.95rem; letter-spacing: 0.5px; border: none !important; }
.excel-table th { color: #8ab4f8; font-weight: 800; text-align: center; padding: 8px 4px; font-size: 0.85rem; letter-spacing: 1px; text-transform: uppercase; }
.excel-table td { padding: 9px 6px; text-align: center; vertical-align: middle; }
.excel-table .td-pos { color: #8ab4f8; font-weight: 700; width: 35px; font-size: 0.95rem; }
.excel-table .td-equipo { text-align: left; font-weight: 800; font-size: 1.02rem; }
.excel-table .team-wrapper { display: flex; align-items: center; gap: 8px; min-width: 0; }
.excel-table .team-wrapper span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.excel-table .team-logo { width: 26px; height: 26px; object-fit: contain; flex-shrink: 0; }
.excel-table .pts-top2 { background-color: #9e11cc !important; color: #ffffff !important; font-weight: 900 !important; border-radius: 4px; }
.excel-table .pts-best3 { background-color: #b76dd0 !important; color: #ffffff !important; font-weight: 900 !important; border-radius: 4px; }
</style>
"""
    
    if modo_movil:
        html_body = f"""{css_style}
<h3 style="color: #ffffff; font-family: 'Montserrat', sans-serif; font-weight: 800; margin-bottom: 8px;">{titulo_grupo}</h3>
<div class="excel-table-container">
<table class="excel-table">
<thead>
<tr>
    <th>POS</th>
    <th style="text-align: left; padding-left: 28px;">EQUIPO</th>
    <th>J</th>
    <th>G:E:P</th>
    <th>DG</th>
    <th>PTS</th>
</tr>
</thead>
<tbody>
"""
        for idx, row in enumerate(datos_grupo):
            if row["Pos"] in [1, 2]:
                pts_class = "pts-top2"
                border_color = "#9e11cc"
            elif row.get("es_mejor_tercero"):
                pts_class = "pts-best3"
                border_color = "#b76dd0"
            else:
                pts_class = ""
                border_color = "transparent"

            row_bg = "#081028" if idx % 2 == 0 else "#0b1a40"

            escudo_val = row.get("escudo")
            img_src = escudo_val if str(escudo_val).startswith("http") else (f"data:image/png;base64,{get_image_base64(escudo_val)}" if get_image_base64(escudo_val) else "")
            img_html = f'<img src="{img_src}" class="team-logo"/>' if img_src else "⚽"

            nombre_completo = row['Equipo']
            nombre_mostrar = ABREVIATURAS.get(nombre_completo, nombre_completo[:4].upper())
            gep_str = f"{row['G']}:{row['E']}:{row['P']}"

            html_body += f"""<tr style="background-color: {row_bg};">
<td class="td-pos"><div style="display: flex; align-items: center; height: 100%;"><div style="flex: 1; text-align: center; padding: 9px 4px;">{row['Pos']}</div><div style="width: 5px; background-color: {border_color}; align-self: stretch;"></div></div></td>
<td class="td-equipo"><div class="team-wrapper">{img_html}<span>{nombre_mostrar}</span></div></td>
<td>{row['J']}</td>
<td>{gep_str}</td>
<td>{row['DG']}</td>
<td class="{pts_class}">{row['Puntos']}</td>
</tr>"""
        html_body += "</tbody></table></div>"
        return html_body

    else:
        html_body = f"""{css_style}
<h3 style="color: #ffffff; font-family: 'Montserrat', sans-serif; font-weight: 800; margin-bottom: 8px;">{titulo_grupo}</h3>
<div class="excel-table-container">
<table class="excel-table">
<thead>
<tr>
    <th>POS</th>
    <th style="text-align: left; padding-left: 28px;">EQUIPO</th>
    <th>J</th><th>G</th><th>E</th><th>P</th>
    <th>GF</th><th>GC</th><th>DG</th><th>PTS</th>
</tr>
</thead>
<tbody>
"""

        for idx, row in enumerate(datos_grupo):
            if row["Pos"] in [1, 2]:
                pts_class = "pts-top2"
                border_color = "#9e11cc"
            elif row.get("es_mejor_tercero"):
                pts_class = "pts-best3"
                border_color = "#b76dd0"
            else:
                pts_class = ""
                border_color = "transparent"

            row_bg = "#081028" if idx % 2 == 0 else "#0b1a40"

            escudo_val = row.get("escudo")
            img_src = escudo_val if str(escudo_val).startswith("http") else (f"data:image/png;base64,{get_image_base64(escudo_val)}" if get_image_base64(escudo_val) else "")
            img_html = f'<img src="{img_src}" class="team-logo"/>' if img_src else "⚽"

            html_body += f"""<tr style="background-color: {row_bg};">
<td class="td-pos"><div style="display: flex; align-items: center; height: 100%;"><div style="flex: 1; text-align: center; padding: 9px 4px;">{row['Pos']}</div><div style="width: 5px; background-color: {border_color}; align-self: stretch;"></div></div></td>
<td class="td-equipo"><div class="team-wrapper">{img_html}<span>{row['Equipo'].upper()}</span></div></td>
<td>{row['J']}</td><td>{row['G']}</td><td>{row['E']}</td><td>{row['P']}</td>
<td>{row['GF']}</td><td>{row['GC']}</td><td>{row['DG']}</td>
<td class="{pts_class}">{row['Puntos']}</td>
</tr>"""
        html_body += "</tbody></table></div>"
        return html_body


# ---------------------------------------------------------
# 5. CONFIGURACIÓN PÁGINA Y ESTILO CHAMPIONS
# ---------------------------------------------------------
st.set_page_config(
    page_title="Champions Mandinguera",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded",
)

INICIO_CM = 1
FIN_CM = 6

custom_css = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@600;700;800;900&display=swap');
    .stApp { background-color: #081028; color: #ffffff; font-family: 'Segoe UI', Roboto, sans-serif; }
    #MainMenu, footer, header {visibility: hidden;}

    div[data-testid="stButton"] > button {
        width: 100% !important; height: 24px !important; background-color: #050c1f !important;
        border: 1px solid rgba(0, 163, 224, 0.4) !important; border-top: none !important; border-radius: 0 0 6px 6px !important;
        color: #ffffff !important; font-size: 1.1rem !important;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# ---------------------------------------------------------
# 6. CABECERA (LOGO 100% CENTRADO MEDIANTE HTML/BASE64)
# ---------------------------------------------------------
if LOGO_PATH.exists():
    img_b64 = get_image_base64(LOGO_PATH)
    st.markdown(
        f"""
        <div style='display: flex; justify-content: center; align-items: center; margin-bottom: 10px;'>
            <img src='data:image/png;base64,{img_b64}' width='140' alt='Logo Champions' />
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.error(f"⚠️ Logo no encontrado en: {LOGO_PATH}")

st.markdown("---")

# ---------------------------------------------------------
# 7. AUTENTICACIÓN Y CARGA DE DATOS
# ---------------------------------------------------------
email = st.secrets.get("FUTMONDO_USER") or st.secrets.get("futmondo", {}).get("email") or "scorderorando@gmail.com"
password = st.secrets.get("FUTMONDO_PASS") or st.secrets.get("futmondo", {}).get("password")
championship_id = st.secrets.get("FUTMONDO_CHAMPIONSHIP_ID") or st.secrets.get("futmondo", {}).get("championship_id") or "5b56e918529e47fd32faea09"

equipos = {}
rounds_info = []
userteam_id = None

if email and password:
    token, userid = login_futmondo(email, password)
    if token and userid:
        equipos = obtener_equipos_liga(token, userid, championship_id)
        if equipos:
            userteam_id = next(iter(equipos.values()))["id"]
            rounds_info = obtener_jornadas_usuario(token, userid, championship_id, userteam_id)

jornada_key_state = "jornada_champions"
if jornada_key_state not in st.session_state:
    st.session_state[jornada_key_state] = INICIO_CM

# ---------------------------------------------------------
# 8. VISTA PRINCIPAL (COLUMNAS)
# ---------------------------------------------------------
col_tabla, col_partidos = st.columns([1.35, 1], gap="medium")

with col_tabla:
    # Botón/Interruptor para alternar la vista móvil compacta
    modo_movil = st.toggle("📱 Vista Compacta (Móvil)", value=False, help="Activa esta opción para ver una tabla resumida sin scroll lateral")

    if equipos and rounds_info and token and userid:
        clasificaciones_grupos = calcular_clasificacion_grupos(
            equipos, rounds_info, token, userid, championship_id, userteam_id, hasta_jornada=FIN_CM
        )
        for nombre_grupo, datos_grupo in clasificaciones_grupos.items():
            html_tabla = render_tabla_grupo(datos_grupo, nombre_grupo, modo_movil=modo_movil)
            st.markdown(html_tabla, unsafe_allow_html=True)
    else:
        st.warning("Cargando datos de la Champions Mandinguera...")

with col_partidos:
    st.markdown('<h3 style="color: #ffffff; font-family: \'Montserrat\', sans-serif; font-weight: 800;">⚽ ENFRENTAMIENTOS</h3>', unsafe_allow_html=True)

    def format_func_jornada(x):
        return f"JORNADA {x} — J{MAPEO_LIGA_REAL.get(x, x)} de Liga"

    jornada_elegida = st.selectbox(
        "Selecciona la Jornada",
        options=list(range(INICIO_CM, FIN_CM + 1)),
        index=st.session_state[jornada_key_state] - INICIO_CM,
        format_func=format_func_jornada,
        key="combo_champions_selector",
        label_visibility="collapsed"
    )

    if jornada_elegida != st.session_state[jornada_key_state]:
        st.session_state[jornada_key_state] = jornada_elegida
        st.rerun()

    partidos_jornada = obtener_partidos_jornada_evaluados(
        jornada_elegida, equipos, rounds_info, token, userid, championship_id, userteam_id
    )

    if partidos_jornada:
        round_mapped_num = MAPEO_LIGA_REAL.get(jornada_elegida, jornada_elegida)
        round_obj = next((r for r in rounds_info if isinstance(r, dict) and r.get("number") == round_mapped_num), None)
        round_id = round_obj.get("id") if round_obj else None
        round_closed = round_obj and round_obj.get("status") == "closed"

        puntos_jornada_sel = {}
        if round_id and token and userid:
            ranking_data = obtener_ranking_jornada(token, userid, championship_id, userteam_id, round_id)
            for item in ranking_data:
                if isinstance(item, dict):
                    nombre_api = item.get("name")
                    pts = item.get("points", 0)
                    info_eq = buscar_equipo_info(nombre_api, equipos)
                    if info_eq and "nombre_equipo" in info_eq:
                        puntos_jornada_sel[info_eq["nombre_equipo"]] = pts

        partidos_por_grupo = {"GRUPO A": [], "GRUPO B": [], "GRUPO C": []}
        for eq1_cal, eq2_cal in partidos_jornada:
            grupo = obtener_grupo_equipo(eq1_cal)
            if not grupo:
                grupo = obtener_grupo_equipo(eq2_cal)
            if grupo in partidos_por_grupo:
                partidos_por_grupo[grupo].append((eq1_cal, eq2_cal))
            else:
                partidos_por_grupo["GRUPO A"].append((eq1_cal, eq2_cal))

        for nombre_grupo, lista_partidos in partidos_por_grupo.items():
            if not lista_partidos:
                continue

            st.markdown(
                f"""
                <div style="background: linear-gradient(90deg, #0b1a40 0%, #132d6b 100%); border-left: 4px solid #00a3e0; padding: 8px 14px; margin-top: 15px; margin-bottom: 10px; border-radius: 4px; font-family: 'Montserrat', sans-serif;">
                    <span style="color: #8ab4f8; font-weight: 800; font-size: 0.95rem; text-transform: uppercase; letter-spacing: 1px;">{nombre_grupo}</span>
                </div>
                """,
                unsafe_allow_html=True
            )

            for nombre1_cal, nombre2_cal in lista_partidos:
                nombre1 = normalizar_nombre_equipo(nombre1_cal)
                nombre2 = normalizar_nombre_equipo(nombre2_cal)
                abrev1 = ABREVIATURAS.get(nombre1_cal, nombre1[:3].upper())
                abrev2 = ABREVIATURAS.get(nombre2_cal, nombre2[:3].upper())

                info1 = buscar_equipo_info(nombre1_cal, equipos)
                info2 = buscar_equipo_info(nombre2_cal, equipos)

                escudo1 = obtener_ruta_escudo(info1.get("id"), info1.get("escudo_url"))
                img_src1 = escudo1 if str(escudo1).startswith("http") else (f"data:image/png;base64,{get_image_base64(escudo1)}" if get_image_base64(escudo1) else "")
                img_html1 = f'<img src="{img_src1}" style="width: 60px; height: 60px; object-fit: contain; flex-shrink: 0;"/>' if img_src1 else "⚽"

                escudo2 = obtener_ruta_escudo(info2.get("id"), info2.get("escudo_url"))
                img_src2 = escudo2 if str(escudo2).startswith("http") else (f"data:image/png;base64,{get_image_base64(escudo2)}" if get_image_base64(escudo2) else "")
                img_html2 = f'<img src="{img_src2}" style="width: 60px; height: 60px; object-fit: contain; flex-shrink: 0;"/>' if img_src2 else "⚽"

                if round_closed:
                    pts1 = puntos_jornada_sel.get(nombre1, 0)
                    pts2 = puntos_jornada_sel.get(nombre2, 0)
                    gf1, gf2 = calcular_goles_partido(pts1, pts2)
                    centro_texto = f"{gf1} - {gf2}"
                    estado_texto = "Finalizado"
                else:
                    centro_texto = "VS"
                    estado_texto = "Por comenzar"

                st.markdown(
                    f"""
                    <div style="background-color: #0b1a40; border: 1px solid rgba(0, 163, 224, 0.4); border-radius: 8px; padding: 12px 18px; margin-bottom: 12px; display: flex; align-items: center; justify-content: space-between; font-family: 'Montserrat', sans-serif;">
                        <div style="display: flex; align-items: center; gap: 12px; width: 38%;">
                            {img_html1}
                            <span style="font-weight: 800; font-size: 1.1rem; color: #ffffff;">{abrev1}</span>
                        </div>
                        <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; width: 24%;">
                            <span style="font-size: 0.65rem; color: #8ab4f8; font-weight: 700; text-transform: uppercase; margin-bottom: 3px;">{estado_texto}</span>
                            <div style="background-color: #050c1f; border: 1px solid rgba(0, 163, 224, 0.4); border-radius: 6px; padding: 4px 14px; font-weight: 900; font-size: 1.25rem; color: #ffffff; letter-spacing: 2px; text-align: center;">
                                {centro_texto}
                            </div>
                        </div>
                        <div style="display: flex; align-items: center; justify-content: flex-end; gap: 12px; width: 38%;">
                            <span style="font-weight: 800; font-size: 1.1rem; color: #ffffff; text-align: right;">{abrev2}</span>
                            {img_html2}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            equipos_grupo = GRUPOS_EQUIPOS.get(nombre_grupo, [])
            jugando_grupo = set()
            for n1, n2 in lista_partidos:
                jugando_grupo.add(normalizar_nombre_equipo(n1))
                jugando_grupo.add(normalizar_nombre_equipo(n2))

            descansa_grupo = [eq for eq in equipos_grupo if normalizar_nombre_equipo(eq) not in jugando_grupo]
            if descansa_grupo:
                eq_desc = descansa_grupo[0]
                info_desc = buscar_equipo_info(eq_desc, equipos)
                escudo_desc = obtener_ruta_escudo(info_desc.get("id"), info_desc.get("escudo_url"))
                img_src_desc = escudo_desc if str(escudo_desc).startswith("http") else (f"data:image/png;base64,{get_image_base64(escudo_desc)}" if get_image_base64(escudo_desc) else "")
                img_html_desc = f'<img src="{img_src_desc}" style="width: 36px; height: 36px; object-fit: contain; flex-shrink: 0;"/>' if img_src_desc else "⚽"

                st.markdown(
                    f"""
                    <div style="background-color: #0b1a40; border: 1px dashed rgba(0, 163, 224, 0.4); border-radius: 6px; padding: 8px 14px; margin-bottom: 15px; display: flex; align-items: center; justify-content: center; gap: 10px; font-family: 'Montserrat', sans-serif;">
                        <span style="font-size: 0.75rem; color: #8ab4f8; font-weight: 800; text-transform: uppercase; letter-spacing: 1px;">DESCANSA:</span>
                        <span style="font-weight: 800; font-size: 0.95rem; color: #ffffff;">{eq_desc.upper()}</span>
                        {img_html_desc}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
    else:
        st.warning("No hay partidos programados para esta jornada.")
