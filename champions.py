# =========================================================
# ARCHIVO: champions.py (Versión 2.4 - Margen compacto a -18px)
# =========================================================

import base64
import json
import re
from pathlib import Path
import requests
import streamlit as st
from concurrent.futures import ThreadPoolExecutor

# ---------------------------------------------------------
# 1. ARCHIVOS Y RUTAS BASE
# ---------------------------------------------------------
BASE_DIR = Path(__file__).parent
ASSETS_DIR = BASE_DIR / "assets"
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
    "Cskalaropa": "CSK",
    "CSKAlaropa": "CSK"
}

EQUIVALENCIAS_NOMBRES = {
    "CSKAlaropa": "Cskalaropa",
    "Cskalaropa": "CSKAlaropa"
}

# Distribución de los 13 equipos en 3 grupos (para Champions)
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


def formatear_nombre_futmondo(nombre_completo):
    """Formatea el nombre al estilo Futmondo (ej. Mario Soriano -> M. Soriano)."""
    if not nombre_completo:
        return "Jugador"
    partes = nombre_completo.strip().split()
    if len(partes) > 1:
        return f"{partes[0][0].upper()}. {' '.join(partes[1:])}"
    return nombre_completo


def obtener_grupo_equipo(nombre_equipo):
    """Devuelve el grupo al que pertenece un equipo (para Champions)."""
    norm_eq = normalizar_nombre_equipo(nombre_equipo)
    for grupo, equipos_lista in GRUPOS_EQUIPOS.items():
        for eq in equipos_lista:
            if normalizar_nombre_equipo(eq).lower() == norm_eq.lower():
                return grupo
    return ""


# ---------------------------------------------------------
# MAPEOS DE JORNADAS CON LA LIGA REAL
# ---------------------------------------------------------
MAPEO_LIGA_REAL_CHAMPIONS = {
    1: 5,
    2: 9,
    3: 10,
    4: 12,
    5: 14,
    6: 16
}

MAPEO_LIGA_REAL_SUPERMANDIGO = {
    1: 1, 2: 2, 3: 3, 4: 4, 5: 6, 6: 7, 7: 8,
    8: 13, 9: 18, 10: 19, 11: 21, 12: 25, 13: 26
}


# ---------------------------------------------------------
# CALENDARIOS OFICIALES
# ---------------------------------------------------------
CALENDARIO_JORNADAS_CHAMPIONS = {
    1: [
        ("Rayo Malayo", "Bass-T-Nation United"),
        ("LA MERIDA GUSTO FC", "Maccabi de Levantá"),
        ("Al-larik-apapa", "Estrella Galicia CF"),
        ("La casa de la Juventus", "AC Poniente"),
        ("Apoel Barceló C.F.", "Olympique de Mamársella"),
        ("Emerita Adisgusta!", "Wine & Horses")
    ],
    2: [
        ("Maccabi de Levantá", "Rayo Malayo"),
        ("Bass-T-Nation United", "LA MERIDA GUSTO FC"),
        ("AC Poniente", "Al-larik-apapa"),
        ("Estrella Galicia CF", "La casa de la Juventus"),
        ("Wine & Horses", "Apoel Barceló C.F."),
        ("Cskalaropa", "Emerita Adisgusta!")
    ],
    3: [
        ("Rayo Malayo", "LA MERIDA GUSTO FC"),
        ("Maccabi de Levantá", "Bass-T-Nation United"),
        ("Al-larik-apapa", "La casa de la Juventus"),
        ("Estrella Galicia CF", "AC Poniente"),
        ("Apoel Barceló C.F.", "Cskalaropa"),
        ("Olympique de Mamársella", "Wine & Horses")
    ],
    4: [
        ("Bass-T-Nation United", "Rayo Malayo"),
        ("Maccabi de Levantá", "LA MERIDA GUSTO FC"),
        ("Estrella Galicia CF", "Al-larik-apapa"),
        ("AC Poniente", "La casa de la Juventus"),
        ("Olympique de Mamársella", "Apoel Barceló C.F."),
        ("Wine & Horses", "Emerita Adisgusta!")
    ],
    5: [
        ("Rayo Malayo", "Maccabi de Levantá"),
        ("LA MERIDA GUSTO FC", "Bass-T-Nation United"),
        ("Al-larik-apapa", "AC Poniente"),
        ("La casa de la Juventus", "Estrella Galicia CF"),
        ("Apoel Barceló C.F.", "Wine & Horses"),
        ("Emerita Adisgusta!", "Cskalaropa")
    ],
    6: [
        ("LA MERIDA GUSTO FC", "Rayo Malayo"),
        ("Bass-T-Nation United", "Maccabi de Levantá"),
        ("La casa de la Juventus", "Al-larik-apapa"),
        ("AC Poniente", "Estrella Galicia CF")
    ]
}

CALENDARIO_JORNADAS_SUPERMANDIGO = {
    1: [
        ("Rayo Malayo", "Emerita Adisgusta!"),
        ("AC Poniente", "Olympique de Mamársella"),
        ("Al-larik-apapa", "Maccabi de Levantá"),
        ("Wine & Horses", "Cskalaropa"),
        ("Bass-T-Nation United", "Estrella Galicia CF"),
        ("LA MERIDA GUSTO FC", "Apoel Barceló C.F.")
    ],
    2: [
        ("Rayo Malayo", "La casa de la Juventus"),
        ("Emerita Adisgusta!", "Al-larik-apapa"),
        ("Olympique de Mamársella", "Wine & Horses"),
        ("Maccabi de Levantá", "Bass-T-Nation United"),
        ("Cskalaropa", "LA MERIDA GUSTO FC"),
        ("Estrella Galicia CF", "Apoel Barceló C.F.")
    ],
    3: [
        ("La casa de la Juventus", "AC Poniente"),
        ("Al-larik-apapa", "Rayo Malayo"),
        ("Bass-T-Nation United", "Emerita Adisgusta!"),
        ("LA MERIDA GUSTO FC", "Olympique de Mamársella"),
        ("Apoel Barceló C.F.", "Maccabi de Levantá"),
        ("Estrella Galicia CF", "Cskalaropa")
    ],
    4: [
        ("Al-larik-apapa", "La casa de la Juventus"),
        ("AC Poniente", "Wine & Horses"),
        ("Rayo Malayo", "Bass-T-Nation United"),
        ("Emerita Adisgusta!", "Apoel Barceló C.F."),
        ("Olympique de Mamársella", "Estrella Galicia CF"),
        ("Maccabi de Levantá", "Cskalaropa")
    ],
    5: [
        ("La casa de la Juventus", "Wine & Horses"),
        ("Bass-T-Nation United", "Al-larik-apapa"),
        ("LA MERIDA GUSTO FC", "AC Poniente"),
        ("Apoel Barceló C.F.", "Rayo Malayo"),
        ("Cskalaropa", "Emerita Adisgusta!"),
        ("Maccabi de Levantá", "Olympique de Mamársella")
    ],
    6: [
        ("Bass-T-Nation United", "La casa de la Juventus"),
        ("Wine & Horses", "LA MERIDA GUSTO FC"),
        ("Al-larik-apapa", "Apoel Barceló C.F."),
        ("AC Poniente", "Estrella Galicia CF"),
        ("Rayo Malayo", "Cskalaropa"),
        ("Emerita Adisgusta!", "Olympique de Mamársella")
    ],
    7: [
        ("La casa de la Juventus", "LA MERIDA GUSTO FC"),
        ("Apoel Barceló C.F.", "Bass-T-Nation United"),
        ("Estrella Galicia CF", "Wine & Horses"),
        ("Cskalaropa", "Al-larik-apapa"),
        ("Maccabi de Levantá", "AC Poniente"),
        ("Olympique de Mamársella", "Rayo Malayo")
    ],
    8: [
        ("Apoel Barceló C.F.", "La casa de la Juventus"),
        ("LA MERIDA GUSTO FC", "Estrella Galicia CF"),
        ("Bass-T-Nation United", "Cskalaropa"),
        ("Wine & Horses", "Maccabi de Levantá"),
        ("Al-larik-apapa", "Olympique de Mamársella"),
        ("AC Poniente", "Emerita Adisgusta!")
    ],
    9: [
        ("La casa de la Juventus", "Estrella Galicia CF"),
        ("Cskalaropa", "Apoel Barceló C.F."),
        ("Maccabi de Levantá", "LA MERIDA GUSTO FC"),
        ("Olympique de Mamársella", "Bass-T-Nation United"),
        ("Emerita Adisgusta!", "Wine & Horses"),
        ("Rayo Malayo", "AC Poniente")
    ],
    10: [
        ("Cskalaropa", "La casa de la Juventus"),
        ("Estrella Galicia CF", "Maccabi de Levantá"),
        ("Apoel Barceló C.F.", "Olympique de Mamársella"),
        ("LA MERIDA GUSTO FC", "Emerita Adisgusta!"),
        ("Wine & Horses", "Rayo Malayo"),
        ("Al-larik-apapa", "AC Poniente")
    ],
    11: [
        ("La casa de la Juventus", "Maccabi de Levantá"),
        ("Olympique de Mamársella", "Cskalaropa"),
        ("Emerita Adisgusta!", "Estrella Galicia CF"),
        ("Rayo Malayo", "LA MERIDA GUSTO FC"),
        ("AC Poniente", "Bass-T-Nation United"),
        ("Al-larik-apapa", "Wine & Horses")
    ],
    12: [
        ("Olympique de Mamársella", "La casa de la Juventus"),
        ("Maccabi de Levantá", "Emerita Adisgusta!"),
        ("Estrella Galicia CF", "Rayo Malayo"),
        ("Apoel Barceló C.F.", "AC Poniente"),
        ("LA MERIDA GUSTO FC", "Al-larik-apapa"),
        ("Bass-T-Nation United", "Wine & Horses")
    ],
    13: [
        ("La casa de la Juventus", "Emerita Adisgusta!"),
        ("Rayo Malayo", "Maccabi de Levantá"),
        ("AC Poniente", "Cskalaropa"),
        ("Al-larik-apapa", "Estrella Galicia CF"),
        ("Wine & Horses", "Apoel Barceló C.F."),
        ("Bass-T-Nation United", "LA MERIDA GUSTO FC")
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
# REGLAS DE CONVERSIÓN DE PUNTOS A GOLES
# ---------------------------------------------------------
def puntos_a_goles_base_champions(pts):
    if pts <= 49: return 0
    elif 50 <= pts <= 69: return 1
    elif 70 <= pts <= 79: return 2
    elif 80 <= pts <= 89: return 3
    elif 90 <= pts <= 99: return 4
    elif 100 <= pts <= 109: return 5
    else: return 5 + (pts - 100) // 10


def calcular_goles_partido_champions(pts1, pts2, aplicar_regla_diferencia=True):
    g1 = puntos_a_goles_base_champions(pts1)
    g2 = puntos_a_goles_base_champions(pts2)
    if aplicar_regla_diferencia and g1 == g2:
        if pts1 > pts2 and (pts1 - pts2) >= 10:
            g1 += 1
        elif pts2 > pts1 and (pts2 - pts1) >= 10:
            g2 += 1
    return g1, g2


def puntos_a_goles_base_supermandingo(pts):
    if pts <= 99: return 0
    elif 100 <= pts <= 119: return 1
    elif 120 <= pts <= 129: return 2
    elif 130 <= pts <= 139: return 3
    elif 140 <= pts <= 149: return 4
    elif 150 <= pts <= 159: return 5
    elif 160 <= pts <= 169: return 6
    elif 170 <= pts <= 179: return 7
    elif 180 <= pts <= 189: return 8
    else: return 8 + (pts - 180) // 10


def calcular_goles_partido_supermandingo(pts1, pts2, aplicar_regla_diferencia=True):
    g1 = puntos_a_goles_base_supermandingo(pts1)
    g2 = puntos_a_goles_base_supermandingo(pts2)
    if aplicar_regla_diferencia and g1 == g2:
        if pts1 > pts2 and (pts1 - pts2) >= 10:
            g1 += 1
        elif pts2 > pts1 and (pts2 - pts1) >= 10:
            g2 += 1
    return g1, g2


# ---------------------------------------------------------
# 2. FUNCIONES API FUTMONDO & CACHÉ
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
        teams_list = data.get("answer", {}).get("teams", [])
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
        return response.json().get("answer", [])
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
        answer = response.json().get("answer", {})
        if isinstance(answer, dict):
            ranking = answer.get("ranking")
            if isinstance(ranking, list):
                return ranking
        return []
    except Exception:
        return []


@st.cache_data(ttl=600, show_spinner=False)
def obtener_round_lineup(token, userid, championship_id, round_id, userteam_id):
    url = "https://api.futmondo.com/1/userteam/roundlineup"
    payload = {
        "header": {"token": token, "userid": userid},
        "query": {
            "championshipId": championship_id,
            "round": round_id,
            "userteamId": userteam_id
        },
        "answer": {}
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return response.json().get("answer", {})
    except Exception:
        return {}


# ---------------------------------------------------------
# 3. CÁLCULO DE CLASIFICACIÓN SUPERMANDINGO (TIPO EXCEL CON FORMA)
# ---------------------------------------------------------
def calcular_clasificacion_supermandingo(equipos_map, rounds_info, token, userid, championship_id, userteam_id):
    stats = {}
    for nombre_eq in equipos_map.keys():
        stats[nombre_eq] = {
            "Equipo": nombre_eq,
            "id": equipos_map[nombre_eq]["id"],
            "escudo": obtener_ruta_escudo(equipos_map[nombre_eq]["id"], equipos_map[nombre_eq].get("escudo_url")),
            "J": 0, "G": 0, "E": 0, "P": 0, "GF": 0, "GC": 0, "DG": 0, "Puntos": 0, "SUM": 0,
            "forma": {}
        }

    jornadas_cerradas = [r for r in rounds_info if isinstance(r, dict) and r.get("status") == "closed"]
    jornadas_cerradas = sorted(jornadas_cerradas, key=lambda x: x.get("number", 0))
    jornadas_jugadas_count = len(jornadas_cerradas)

    for r in jornadas_cerradas:
        num_jornada = r.get("number")
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

        partidos = CALENDARIO_JORNADAS_SUPERMANDIGO.get(num_jornada, [])
        for eq1_cal, eq2_cal in partidos:
            eq1 = normalizar_nombre_equipo(eq1_cal)
            eq2 = normalizar_nombre_equipo(eq2_cal)

            if eq1 in stats and eq2 in stats:
                pts1 = puntos_fantasy.get(eq1, 0)
                pts2 = puntos_fantasy.get(eq2, 0)

                stats[eq1]["SUM"] += pts1
                stats[eq2]["SUM"] += pts2

                gf1, gf2 = calcular_goles_partido_supermandingo(pts1, pts2, aplicar_regla_diferencia=True)

                if gf1 > gf2: res_letra1, res_letra2 = "G", "P"
                elif gf1 < gf2: res_letra1, res_letra2 = "P", "G"
                else: res_letra1, res_letra2 = "E", "E"

                stats[eq1]["J"] += 1; stats[eq1]["GF"] += gf1; stats[eq1]["GC"] += gf2
                if gf1 > gf2: stats[eq1]["G"] += 1; stats[eq1]["Puntos"] += 3
                elif gf1 == gf2: stats[eq1]["E"] += 1; stats[eq1]["Puntos"] += 1
                else: stats[eq1]["P"] += 1
                stats[eq1]["forma"][num_jornada] = res_letra1

                stats[eq2]["J"] += 1; stats[eq2]["GF"] += gf2; stats[eq2]["GC"] += gf1
                if gf2 > gf1: stats[eq2]["G"] += 1; stats[eq2]["Puntos"] += 3
                elif gf2 == gf1: stats[eq2]["E"] += 1; stats[eq2]["Puntos"] += 1
                else: stats[eq2]["P"] += 1
                stats[eq2]["forma"][num_jornada] = res_letra2

    lista_clasif = []
    for data in stats.values():
        data["DG"] = data["GF"] - data["GC"]
        lista_clasif.append(data)

    lista_clasif = sorted(lista_clasif, key=lambda x: (x["Puntos"], x["DG"], x["GF"], x["SUM"]), reverse=True)
    for idx, row in enumerate(lista_clasif):
        row["Pos"] = idx + 1

    return lista_clasif, jornadas_jugadas_count


def render_tabla_clasificacion_supermandingo(datos_clasificacion, jornada_sel, modo_movil=False):
    jornadas_forma = []
    for i in range(5):
        j = jornada_sel - i
        jornadas_forma.append(j if j >= 1 else None)

    total_equipos = len(datos_clasificacion)

    css_style = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@600;700;800;900&display=swap');
.excel-table-container { width: 100%; overflow-x: auto; margin-top: -3px; background: #354d47; border-radius: 8px; padding: 8px; border: none !important; box-sizing: border-box; }
.excel-table { width: 100%; border-collapse: collapse; font-family: 'Montserrat', sans-serif; color: #ffffff; font-size: 0.95rem; letter-spacing: 0.5px; border: none !important; }
.excel-table th, .excel-table td { border: none !important; }
.excel-table th { color: #8aa4ae; font-weight: 800; text-align: center; padding: 5px 4px; font-size: 0.85rem; letter-spacing: 1px; text-transform: uppercase; }
.excel-table td { padding: 9px 6px; text-align: center; vertical-align: middle; }
.excel-table .td-pos { color: #8aa4ae; font-weight: 700; width: 35px; font-size: 0.95rem; padding: 0 !important; }
.excel-table .td-equipo { text-align: left; font-weight: 800; font-size: 1.02rem; }
.excel-table .team-wrapper { display: flex; align-items: center; gap: 8px; min-width: 0; }
.excel-table .team-wrapper span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.excel-table .team-logo { width: 26px; height: 26px; object-fit: contain; flex-shrink: 0; }
.excel-table .pts-green { background-color: #277e3c !important; color: #ffffff !important; font-weight: 900 !important; font-size: 1.1rem !important; border-radius: 4px; }
.excel-table .pts-gold { background-color: #b58100 !important; color: #ffffff !important; font-weight: 900 !important; font-size: 1.1rem !important; border-radius: 4px; }
.excel-table .pts-red { background-color: #c0392b !important; color: #ffffff !important; font-weight: 900 !important; font-size: 1.1rem !important; border-radius: 4px; }

.form-badge { width: 24px; height: 24px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-size: 0.75rem; font-weight: 900; margin: 0 auto; box-sizing: border-box; }
.form-win { background-color: #27ae60; color: #ffffff; border: 2px solid #27ae60; }
.form-draw { background-color: #7f8c8d; color: #ffffff; border: 2px solid #7f8c8d; }
.form-loss { background-color: #e74c3c; color: #ffffff; border: 2px solid #e74c3c; }
.form-empty { background-color: transparent; border: 2px solid #7f8c8d; width: 22px; height: 22px; color: transparent; }
</style>
"""

    if modo_movil:
        html_body = f"""{css_style}
<div class="excel-table-container">
<table class="excel-table">
<thead>
<tr>
    <th rowspan="2">POS</th>
    <th rowspan="2" style="text-align: left; padding-left: 28px;">EQUIPO</th>
    <th rowspan="2">J</th><th rowspan="2">G:E:P</th><th rowspan="2">DG</th><th rowspan="2">PTS</th>
</tr>
<tr></tr></thead><tbody>"""
        for idx, row in enumerate(datos_clasificacion):
            if row["Pos"] == total_equipos: pts_class = "pts-red"; border_color = "#c0392b"
            elif row["Pos"] <= 8: pts_class = "pts-green"; border_color = "#277e3c"
            else: pts_class = "pts-gold"; border_color = "#b58100"

            row_bg = "#151e19" if idx % 2 == 0 else "#354d47"
            escudo_val = row.get("escudo")
            img_src = escudo_val if str(escudo_val).startswith("http") else (f"data:image/png;base64,{get_image_base64(escudo_val)}" if get_image_base64(escudo_val) else "")
            img_html = f'<img src="{img_src}" class="team-logo"/>' if img_src else "⚽"
            
            nombre_mostrar = ABREVIATURAS.get(row['Equipo'], row['Equipo'][:4].upper())
            gep_str = f"{row['G']}:{row['E']}:{row['P']}"

            html_body += f"""<tr style="background-color: {row_bg};">
<td class="td-pos">
    <div style="display: flex; align-items: center; height: 100%;">
        <div style="flex: 1; text-align: center; padding: 9px 4px;">{row['Pos']}</div>
        <div style="width: 5px; background-color: {border_color}; align-self: stretch; min-height: 38px;"></div>
    </div>
</td>
<td class="td-equipo"><div class="team-wrapper">{img_html}<span style="font-weight: 600;">{nombre_mostrar}</span></div></td>
<td>{row['J']}</td><td>{gep_str}</td><td>{row['DG']}</td>
<td class="{pts_class}">{row['Puntos']}</td>
</tr>"""
        html_body += "</tbody></table></div>"
        return html_body

    else:
        html_body = f"""{css_style}
<div class="excel-table-container">
<table class="excel-table">
<thead>
<tr>
    <th rowspan="2">POS</th>
    <th rowspan="2" style="text-align: left; padding-left: 28px;">EQUIPO</th>
    <th rowspan="2">J</th><th rowspan="2">G</th><th rowspan="2">E</th><th rowspan="2">P</th>
    <th rowspan="2">GF</th><th rowspan="2">GC</th><th rowspan="2">DG</th><th rowspan="2">PTS</th>
    <th colspan="{len(jornadas_forma)}">FORMA</th>
</tr>
<tr>
"""
        for j in jornadas_forma:
            html_body += f"<th>J{j}</th>" if j is not None else "<th>-</th>"
        html_body += "</tr></thead><tbody>"

        for idx, row in enumerate(datos_clasificacion):
            if row["Pos"] == total_equipos: pts_class = "pts-red"; border_color = "#c0392b"
            elif row["Pos"] <= 8: pts_class = "pts-green"; border_color = "#277e3c"
            else: pts_class = "pts-gold"; border_color = "#b58100"

            row_bg = "#151e19" if idx % 2 == 0 else "#354d47"

            forma_dots_html = ""
            for j in jornadas_forma:
                if j is None:
                    forma_dots_html += '<td><span class="form-badge form-empty"></span></td>'
                else:
                    resultado = row.get("forma", {}).get(j)
                    if resultado == "G": forma_dots_html += '<td><span class="form-badge form-win">✓</span></td>'
                    elif resultado == "E": forma_dots_html += '<td><span class="form-badge form-draw">-</span></td>'
                    elif resultado == "P": forma_dots_html += '<td><span class="form-badge form-loss">×</span></td>'
                    else: forma_dots_html += '<td><span class="form-badge form-empty"></span></td>'

            escudo_val = row.get("escudo")
            img_src = escudo_val if str(escudo_val).startswith("http") else (f"data:image/png;base64,{get_image_base64(escudo_val)}" if get_image_base64(escudo_val) else "")
            img_html = f'<img src="{img_src}" class="team-logo"/>' if img_src else "⚽"

            html_body += f"""<tr style="background-color: {row_bg};">
<td class="td-pos">
    <div style="display: flex; align-items: center; height: 100%;">
        <div style="flex: 1; text-align: center; padding: 9px 4px;">{row['Pos']}</div>
        <div style="width: 5px; background-color: {border_color}; align-self: stretch; min-height: 38px;"></div>
    </div>
</td>
<td class="td-equipo"><div class="team-wrapper">{img_html}<span>{row['Equipo'].upper()}</span></div></td>
<td>{row['J']}</td><td>{row['G']}</td><td>{row['E']}</td><td>{row['P']}</td>
<td>{row['GF']}</td><td>{row['GC']}</td><td>{row['DG']}</td>
<td class="{pts_class}">{row['Puntos']}</td>
{forma_dots_html}
</tr>"""
        html_body += "</tbody></table></div>"
        return html_body


# ---------------------------------------------------------
# 4. CÁLCULO DE CLASIFICACIÓN CHAMPIONS (POR GRUPOS)
# ---------------------------------------------------------
def calcular_clasificacion_grupos_champions(equipos_map, rounds_info, token, userid, championship_id, userteam_id, hasta_jornada=6):
    stats = {}
    for nombre_eq in equipos_map.keys():
        stats[nombre_eq] = {
            "Equipo": nombre_eq,
            "id": equipos_map[nombre_eq]["id"],
            "escudo": obtener_ruta_escudo(equipos_map[nombre_eq]["id"], equipos_map[nombre_eq].get("escudo_url")),
            "J": 0, "G": 0, "E": 0, "P": 0, "GF": 0, "GC": 0, "DG": 0, "Puntos": 0, "SUM": 0
        }

    jornadas_cerradas = [r for r in rounds_info if isinstance(r, dict) and r.get("status") == "closed"]
    jornadas_cerradas = sorted(jornadas_cerradas, key=lambda x: x.get("number", 0))

    for r in jornadas_cerradas:
        num_jornada = r.get("number")
        if num_jornada > hasta_jornada: continue
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

        partidos = obtener_partidos_jornada_evaluados_champions(num_jornada, equipos_map, rounds_info, token, userid, championship_id, userteam_id)
        for eq1_cal, eq2_cal in partidos:
            eq1 = normalizar_nombre_equipo(eq1_cal)
            eq2 = normalizar_nombre_equipo(eq2_cal)

            if eq1 in stats and eq2 in stats:
                pts1 = puntos_fantasy.get(eq1, 0)
                pts2 = puntos_fantasy.get(eq2, 0)
                stats[eq1]["SUM"] += pts1
                stats[eq2]["SUM"] += pts2

                gf1, gf2 = calcular_goles_partido_champions(pts1, pts2, aplicar_regla_diferencia=True)
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

    for eq_key in stats:
        stats[eq_key]["DG"] = stats[eq_key]["GF"] - stats[eq_key]["GC"]

    clasificaciones_grupos = {}
    for nombre_grupo, lista_nombres_eqs in GRUPOS_EQUIPOS.items():
        grupo_stats = []
        for eq_nombre in lista_nombres_eqs:
            matched_key = next((k for k in stats.keys() if k.lower() == eq_nombre.lower()), None)
            if matched_key and matched_key in stats:
                grupo_stats.append(stats[matched_key])
            else:
                grupo_stats.append({
                    "Equipo": eq_nombre, "id": None, "escudo": None,
                    "J": 0, "G": 0, "E": 0, "P": 0, "GF": 0, "GC": 0, "DG": 0, "Puntos": 0, "SUM": 0
                })
        grupo_stats = sorted(grupo_stats, key=lambda x: (x["Puntos"], x["DG"], x["GF"], x["SUM"]), reverse=True)
        for idx, row in enumerate(grupo_stats):
            row["Pos"] = idx + 1
        clasificaciones_grupos[nombre_grupo] = grupo_stats

    terceros = [g[2] for g in clasificaciones_grupos.values() if len(g) >= 3]
    terceros_ordenados = sorted(terceros, key=lambda x: (x["Puntos"], x["DG"], x["GF"], x["SUM"]), reverse=True)
    mejores_terceros_nombres = {t["Equipo"] for t in terceros_ordenados[:2]}

    for grupo_stats in clasificaciones_grupos.values():
        for row in grupo_stats:
            row["es_mejor_tercero"] = (row["Pos"] == 3 and row["Equipo"] in mejores_terceros_nombres)

    return clasificaciones_grupos


def obtener_partidos_jornada_evaluados_champions(num_jornada, equipos_map, rounds_info, token, userid, championship_id, userteam_id):
    partidos_base = CALENDARIO_JORNADAS_CHAMPIONS.get(num_jornada, [])
    if num_jornada != 6 or not equipos_map or not rounds_info or not token or not userid:
        return partidos_base

    clasificacion_hasta_5 = calcular_clasificacion_grupos_champions(equipos_map, rounds_info, token, userid, championship_id, userteam_id, hasta_jornada=5)
    grupo_c_stats = clasificacion_hasta_5.get("GRUPO C", [])
    partidos_j6_c = []
    if len(grupo_c_stats) >= 4:
        partidos_j6_c.append((grupo_c_stats[0]["Equipo"], grupo_c_stats[3]["Equipo"]))
        partidos_j6_c.append((grupo_c_stats[1]["Equipo"], grupo_c_stats[2]["Equipo"]))

    partidos_ab = [p for p in partidos_base if obtener_grupo_equipo(p[0]) in ["GRUPO A", "GRUPO B"]]
    return partidos_ab + partidos_j6_c


def render_tabla_grupo_champions(datos_grupo, titulo_grupo, modo_movil=False):
    css_style = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@500;600;700;800;900&display=swap');
.excel-table-container { width: 100%; overflow-x: auto; margin-top: -3px; background: #0b1a40; border-radius: 8px; padding: 8px; border: none !important; box-sizing: border-box; margin-bottom: 20px; }
.excel-table { width: 100%; border-collapse: collapse; font-family: 'Montserrat', sans-serif; color: #ffffff; font-size: 0.95rem; letter-spacing: 0.5px; border: none !important; }
.excel-table th { color: #8ab4f8; font-weight: 800; text-align: center; padding: 8px 4px; font-size: 0.85rem; letter-spacing: 1px; text-transform: uppercase; border: none !important; }
.excel-table td { padding: 9px 6px; text-align: center; vertical-align: middle; border: none !important; }
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
<div class="excel-table-container"><table class="excel-table"><thead><tr>
<th colspan="2" style="text-align: left; color: #ffffff; padding-left: 8px; font-weight: 900;">{titulo_grupo}</th>
<th>J</th><th>G:E:P</th><th>DG</th><th>PTS</th>
</tr></thead><tbody>"""
        for idx, row in enumerate(datos_grupo):
            pts_class = "pts-top2" if row["Pos"] in [1, 2] else ("pts-best3" if row.get("es_mejor_tercero") else "")
            border_color = "#9e11cc" if row["Pos"] in [1, 2] else ("#b76dd0" if row.get("es_mejor_tercero") else "transparent")
            row_bg = "#081028" if idx % 2 == 0 else "#0b1a40"
            escudo_val = row.get("escudo")
            img_src = escudo_val if str(escudo_val).startswith("http") else (f"data:image/png;base64,{get_image_base64(escudo_val)}" if get_image_base64(escudo_val) else "")
            img_html = f'<img src="{img_src}" class="team-logo"/>' if img_src else "⚽"
            nombre_mostrar = ABREVIATURAS.get(row['Equipo'], row['Equipo'][:4].upper())
            gep_str = f"{row['G']}:{row['E']}:{row['P']}"
            html_body += f"""<tr style="background-color: {row_bg};">
<td class="td-pos"><div style="display: flex; align-items: center; height: 100%;"><div style="flex: 1; text-align: center; padding: 9px 4px;">{row['Pos']}</div><div style="width: 5px; background-color: {border_color}; align-self: stretch;"></div></div></td>
<td class="td-equipo"><div class="team-wrapper">{img_html}<span style="font-weight: 600;">{nombre_mostrar}</span></div></td>
<td>{row['J']}</td><td>{gep_str}</td><td>{row['DG']}</td><td class="{pts_class}">{row['Puntos']}</td></tr>"""
        html_body += "</tbody></table></div>"
        return html_body
    else:
        html_body = f"""{css_style}
<div class="excel-table-container"><table class="excel-table"><thead><tr>
<th colspan="2" style="text-align: left; color: #ffffff; padding-left: 8px; font-weight: 900;">{titulo_grupo}</th>
<th>J</th><th>G</th><th>E</th><th>P</th><th>GF</th><th>GC</th><th>DG</th><th>PTS</th>
</tr></thead><tbody>"""
        for idx, row in enumerate(datos_grupo):
            pts_class = "pts-top2" if row["Pos"] in [1, 2] else ("pts-best3" if row.get("es_mejor_tercero") else "")
            border_color = "#9e11cc" if row["Pos"] in [1, 2] else ("#b76dd0" if row.get("es_mejor_tercero") else "transparent")
            row_bg = "#081028" if idx % 2 == 0 else "#0b1a40"
            escudo_val = row.get("escudo")
            img_src = escudo_val if str(escudo_val).startswith("http") else (f"data:image/png;base64,{get_image_base64(escudo_val)}" if get_image_base64(escudo_val) else "")
            img_html = f'<img src="{img_src}" class="team-logo"/>' if img_src else "⚽"
            html_body += f"""<tr style="background-color: {row_bg};">
<td class="td-pos"><div style="display: flex; align-items: center; height: 100%;"><div style="flex: 1; text-align: center; padding: 9px 4px;">{row['Pos']}</div><div style="width: 5px; background-color: {border_color}; align-self: stretch;"></div></div></td>
<td class="td-equipo"><div class="team-wrapper">{img_html}<span>{row['Equipo'].upper()}</span></div></td>
<td>{row['J']}</td><td>{row['G']}</td><td>{row['E']}</td><td>{row['P']}</td>
<td>{row['GF']}</td><td>{row['GC']}</td><td>{row['DG']}</td><td class="{pts_class}">{row['Puntos']}</td></tr>"""
        html_body += "</tbody></table></div>"
        return html_body


# ---------------------------------------------------------
# 5. CONFIGURACIÓN PÁGINA Y ESTILOS
# ---------------------------------------------------------
st.set_page_config(
    page_title="Competiciones Futmondo",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded",
)

email = st.secrets.get("FUTMONDO_USER") or st.secrets.get("futmondo", {}).get("email") or "scorderorando@gmail.com"
password = st.secrets.get("FUTMONDO_PASS") or st.secrets.get("futmondo", {}).get("password")

COMPETICIONES = {
    "liga": {
        "nombre": "Liga",
        "championship_id": st.secrets.get("FUTMONDO_LIGA_ID") or st.secrets.get("futmondo", {}).get("liga_id", "5b56e918529e47fd32faea09"),
        "logo": ASSETS_DIR / "logo-liga.png"
    },
    "supermandigo": {
        "nombre": "Supermandigo League",
        "championship_id": st.secrets.get("FUTMONDO_SUPERMANDIGO_ID") or st.secrets.get("futmondo", {}).get("supermandigo_id", "5b56e918529e47fd32faea09"),
        "logo": ASSETS_DIR / "The-Super-Mandingo-League-Logo.png"
    },
    "champions": {
        "nombre": "Champions Mandinguera",
        "championship_id": st.secrets.get("FUTMONDO_CHAMPIONSHIP_ID") or st.secrets.get("futmondo", {}).get("championship_id", "5b56e918529e47fd32faea09"),
        "logo": ASSETS_DIR / "Champions.png"
    },
    "copa": {
        "nombre": "Copa SeCadi,Ok?",
        "championship_id": st.secrets.get("FUTMONDO_COPA_ID") or st.secrets.get("futmondo", {}).get("copa_id", "5b56e918529e47fd32faea09"),
        "logo": ASSETS_DIR / "Logo_Copa.png"
    },
    "2girls1cup": {
        "nombre": "The 2Girls 1Cup",
        "championship_id": st.secrets.get("FUTMONDO_2GIRLS_ID") or st.secrets.get("futmondo", {}).get("2girls_id", "5b56e918529e47fd32faea09"),
        "logo": ASSETS_DIR / "The-2-Girls-1-Cup-Logo.png"
    },
    "supercopa": {
        "nombre": "Supercopa de Campeones",
        "championship_id": st.secrets.get("FUTMONDO_SUPERCOPA_ID") or st.secrets.get("futmondo", {}).get("supercopa_id", "5b56e918529e47fd32faea09"),
        "logo": ASSETS_DIR / "Supercopa-Logo-vertical.png"
    }
}

if "competicion_activa" not in st.session_state:
    st.session_state["competicion_activa"] = "liga"

if "comp" in st.query_params:
    comp_val = st.query_params["comp"]
    if comp_val in COMPETICIONES and st.session_state["competicion_activa"] != comp_val:
        st.session_state["competicion_activa"] = comp_val

if "modo_compacto" not in st.session_state:
    if "compact" in st.query_params:
        st.session_state["modo_compacto"] = (st.query_params["compact"] == "1")
    else:
        headers = getattr(st, "context", None) and getattr(st.context, "headers", {})
        user_agent = headers.get("User-Agent", "").lower() if headers else ""
        st.session_state["modo_compacto"] = any(k in user_agent for k in ["mobi", "android", "iphone", "ipad", "ipod"])

def actualizar_modo_compacto():
    st.query_params["compact"] = "1" if st.session_state["modo_compacto"] else "0"

bg_colors = {
    "liga": "#000000",
    "supermandigo": "#11191d",
    "champions": "#081028",
    "copa": "#e4002b",
    "2girls1cup": "#7f6000",
    "supercopa": "#37004d"
}

color_fondo_actual = bg_colors.get(st.session_state["competicion_activa"], "#081028")

# Definir el margen del botón dinámicamente: -18px si está en modo compacto, -24px si está desactivado
margin_top_botón = "-18px" if st.session_state.get("modo_compacto", False) else "-24px"

custom_css = f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@600;700;800;900&display=swap');
    .stApp {{ background-color: {color_fondo_actual}; color: #ffffff; font-family: 'Segoe UI', Roboto, sans-serif; }}
    #MainMenu, footer, header {{visibility: hidden;}}
    .mobile-title {{ display: none; }}
    .desktop-title {{ display: block; }}

    .match-container {{
        background-color: #354d47; border: 1px solid #8aa4ae; border-radius: 8px;
        padding: 14px 18px; display: flex; align-items: center; justify-content: space-between;
        min-height: 95px; box-sizing: border-box; width: 100%; margin-bottom: 14px;
    }}
    .match-team {{ display: flex; align-items: center; gap: 12px; width: 35%; font-weight: 800; font-size: 1.15rem; }}
    .match-team.right {{ justify-content: flex-end; text-align: right; }}
    .match-center {{ text-align: center; width: 30%; display: flex; flex-direction: column; justify-content: center; align-items: center; }}
    .score-box {{
        background-color: #23322e; border: 1px solid #8aa4ae; border-radius: 8px;
        padding: 0 24px; height: 60px; display: flex; align-items: center; justify-content: center;
        font-weight: 900; font-size: 2.3rem; letter-spacing: 3px; color: #ffffff;
    }}

    div[data-testid="stButton"] {{ width: 100% !important; margin-top: {margin_top_botón} !important; z-index: 5 !important; }}
    div[data-testid="stButton"] > button {{
        width: 100% !important; height: 24px !important; min-height: 24px !important;
        background-color: #23322e !important; border: 1px solid #8aa4ae !important; border-top: none !important;
        border-radius: 0 0 6px 6px !important; color: #ffffff !important;
    }}

    .lineup-unified-card {{ background-color: #354d47; border: 1px solid #8aa4ae; border-radius: 8px; padding: 14px 18px; margin-bottom: 14px; }}
    .fields-flex-container {{ display: flex; gap: 12px; width: 100%; }}
    .soccer-field {{
        background: linear-gradient(135deg, #236136 0%, #154222 100%); border: 2px solid rgba(255, 255, 255, 0.4);
        border-radius: 8px; padding: 38px 6px 12px 6px; position: relative; display: flex; flex-direction: column;
        justify-content: space-between; min-height: 380px; box-sizing: border-box;
    }}
    .field-line-center {{ position: absolute; top: 50%; left: 0; right: 0; height: 1px; background: rgba(255, 255, 255, 0.3); }}
    .field-header-top-left {{ position: absolute; top: 8px; left: 10px; display: flex; align-items: center; gap: 6px; z-index: 5; background: rgba(0,0,0,0.4); padding: 3px 8px; border-radius: 4px; }}
    .field-header-top-right {{ position: absolute; top: 8px; right: 10px; font-weight: 900; font-size: 0.85rem; color: #2ecc71; z-index: 5; background: rgba(0,0,0,0.6); padding: 3px 8px; border-radius: 4px; }}
    .field-row {{ display: flex; justify-content: center; gap: 6px; z-index: 2; margin: 4px 0; width: 100%; }}
    .player-card {{ background: rgba(0, 0, 0, 0.75); border: 1px solid rgba(255, 255, 255, 0.3); border-radius: 6px; padding: 4px 5px; text-align: center; max-width: 78px; min-width: 54px; }}
    .player-name {{ font-size: 0.62rem; color: #ffffff; font-weight: 700; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
    .player-pts {{ width: 24px; height: 24px; border-radius: 50%; background-color: #2ecc71; color: #151e19; font-size: 0.68rem; font-weight: 900; display: flex; align-items: center; justify-content: center; margin: 3px auto 0 auto; }}
    .player-pts-zero {{ background-color: #3b524b !important; color: #b0c4de !important; }}
    .player-pts-captain {{ background-color: #f1c40f !important; color: #151e19 !important; }}

    @media (max-width: 768px) {{
        .block-container {{ padding: 0.2rem 0.8rem !important; }}
        .mobile-title {{ display: block; font-size: 1.35rem !important; }}
        .desktop-title {{ display: none; }}
        .fields-flex-container {{ flex-direction: column !important; }}
    }}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# INYECCIÓN CSS GLOBAL PARA EL MODO COMPACTO
if st.session_state.get("modo_compacto", False):
    st.markdown("""
    <style>
    .match-container { min-height: 60px !important; padding: 8px 12px !important; margin-bottom: 8px !important; }
    .match-team { font-size: 0.90rem !important; gap: 6px !important; }
    .match-team img { width: 30px !important; height: 30px !important; }
    .score-box { height: 36px !important; padding: 0 12px !important; font-size: 1.3rem !important; }
    .match-center div { font-size: 0.65rem !important; }
    .lineup-unified-card { padding: 8px 10px !important; }
    .soccer-field { min-height: 280px !important; padding: 25px 4px 8px 4px !important; }
    .player-card { max-width: 50px !important; min-width: 38px !important; padding: 2px 3px !important; }
    .player-name { font-size: 0.5rem !important; }
    .player-pts { width: 18px !important; height: 18px !important; font-size: 0.55rem !important; margin: 2px auto 0 auto !important; }
    .field-header-top-left span { font-size: 0.65rem !important; }
    .field-header-top-right { font-size: 0.75rem !important; padding: 2px 6px !important; }
    </style>
    """, unsafe_allow_html=True)


# Título principal
st.markdown(
    """
    <div style="text-align: center; font-family: 'Montserrat', sans-serif; font-weight: 900; margin-bottom: 20px;">
        <div class="desktop-title" style='color: #ffffff; font-size: 2.2rem; letter-spacing: 1px; margin: 0;'>🏆 COMPETICIONES MANDINGUERAS 2026/27 🏆</div>
        <div class="mobile-title" style='color: #ffffff; letter-spacing: 1px; margin: 0;'>🏆<br>COMPETICIONES<br>MANDINGUERAS<br>2026/27</div>
    </div>
    """,
    unsafe_allow_html=True
)

# Render tarjetas competiciones
def render_tarjetas_competiciones_html():
    border_colors = {
        "liga": "#2f4048", "supermandigo": "#8aa4ae", "champions": "#9e11cc",
        "copa": "#1c0e30", "2girls1cup": "#ffff00", "supercopa": "#fc7e00"
    }
    compact_param = "1" if st.session_state.get("modo_compacto", False) else "0"
    html = """<style>
    .comp-grid { display: grid; grid-template-columns: repeat(6, 1fr); gap: 10px; margin-bottom: 20px; }
    @media (max-width: 900px) { .comp-grid { grid-template-columns: repeat(3, 1fr); } }
    @media (max-width: 600px) { .comp-grid { grid-template-columns: repeat(2, 1fr); } }
    .comp-card { border-radius: 8px; height: 95px; display: flex; align-items: center; justify-content: center; text-decoration: none !important; padding: 8px; box-sizing: border-box; }
    .comp-card img { max-height: 75px; max-width: 100%; object-fit: contain; }
    </style><div class="comp-grid">"""
    
    for key, comp_info in COMPETICIONES.items():
        is_activo = st.session_state["competicion_activa"] == key
        bg = bg_colors.get(key, "#0b1a40")
        border = border_colors.get(key, "#9e11cc")
        card_style = f"background-color: {bg}; border: {'3px solid ' + border if is_activo else '1px solid rgba(255,255,255,0.15)'} !important;"
        img_b64 = get_image_base64(comp_info["logo"]) if comp_info["logo"].exists() else ""
        img_tag = f'<img src="data:image/png;base64,{img_b64}"/>' if img_b64 else f'<span style="color:white;">{comp_info["nombre"]}</span>'
        html += f'<a href="?comp={key}&compact={compact_param}" target="_self" class="comp-card" style="{card_style}">{img_tag}</a>'
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

headers_ua = getattr(st, "context", None) and getattr(st.context, "headers", {})
ua_str = headers_ua.get("User-Agent", "").lower() if headers_ua else ""
if any(k in ua_str for k in ["mobi", "android", "iphone", "ipad"]):
    with st.expander("COMPETICIONES", expanded=False):
        render_tarjetas_competiciones_html()
else:
    st.markdown('<h4 style="color: #8ab4f8; font-family: \'Montserrat\', sans-serif; font-weight: 800; margin-bottom: 10px;">COMPETICIONES</h4>', unsafe_allow_html=True)
    render_tarjetas_competiciones_html()

# Selector de "Modo compacto" condicional (Solo se muestra en Liga, Supermandigo o Champions)
if st.session_state["competicion_activa"] in ["liga", "supermandigo", "champions"]:
    st.toggle("Modo compacto", key="modo_compacto", on_change=actualizar_modo_compacto)

st.markdown("---")

# Definir la competición activa antes de verificar el modo móvil/compacto
comp_actual = COMPETICIONES[st.session_state["competicion_activa"]]
championship_id = comp_actual["championship_id"]
activa = st.session_state["competicion_activa"]

# Si está en modo compacto (móvil) y la competición activa lo soporta, mostrar el logo debajo de la línea separadora en 60px
if st.session_state.get("modo_compacto", False) and activa in ["liga", "supermandigo", "champions"]:
    logo_path = comp_actual.get("logo")
    if logo_path and logo_path.exists():
        logo_b64 = get_image_base64(logo_path)
        if logo_b64:
            st.markdown(f"""
            <div style="text-align: center; margin-bottom: 15px;">
                <img src="data:image/png;base64,{logo_b64}" style="max-height: 60px; object-fit: contain;" />
            </div>
            """, unsafe_allow_html=True)


# =========================================================
# 6. SECCIÓN CHAMPIONS MANDINGUERA
# =========================================================
if activa == "champions":
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
        st.session_state[jornada_key_state] = 1

    col_tabla, col_partidos = st.columns([1.35, 1], gap="medium")

    with col_tabla:
        st.markdown('<h3 style="color: #ffffff; font-family: \'Montserrat\', sans-serif; font-size: 1.2rem; font-weight: 800; margin-bottom: 10px;">📊 GRUPOS</h3>', unsafe_allow_html=True)
            
        if equipos and rounds_info and token and userid:
            modo_movil = st.session_state.get("modo_compacto", False)
            clasificaciones_grupos = calcular_clasificacion_grupos_champions(equipos, rounds_info, token, userid, championship_id, userteam_id, hasta_jornada=6)
            for nombre_grupo, datos_grupo in clasificaciones_grupos.items():
                st.markdown(render_tabla_grupo_champions(datos_grupo, nombre_grupo, modo_movil=modo_movil), unsafe_allow_html=True)
        else:
            st.warning("Cargando datos de Champions...")

    with col_partidos:
        st.markdown('<h3 style="color: #ffffff; font-family: \'Montserrat\', sans-serif; font-weight: 800;">⚽ ENFRENTAMIENTOS</h3>', unsafe_allow_html=True)
        jornada_elegida = st.selectbox(
            "Selecciona la Jornada", options=list(range(1, 7)),
            index=st.session_state[jornada_key_state] - 1,
            format_func=lambda x: f"JORNADA {x} — J{MAPEO_LIGA_REAL_CHAMPIONS.get(x, x)} de Liga",
            key="combo_champions_selector", label_visibility="collapsed"
        )
        if jornada_elegida != st.session_state[jornada_key_state]:
            st.session_state[jornada_key_state] = jornada_elegida
            st.rerun()

        partidos_jornada = obtener_partidos_jornada_evaluados_champions(jornada_elegida, equipos, rounds_info, token, userid, championship_id, userteam_id)
        if partidos_jornada:
            round_mapped_num = MAPEO_LIGA_REAL_CHAMPIONS.get(jornada_elegida, jornada_elegida)
            round_obj = next((r for r in rounds_info if isinstance(r, dict) and r.get("number") == round_mapped_num), None)
            round_id = round_obj.get("id") if round_obj else None
            round_closed = round_obj and round_obj.get("status") == "closed"

            puntos_jornada_sel = {}
            if round_id and token and userid:
                for item in obtener_ranking_jornada(token, userid, championship_id, userteam_id, round_id):
                    info_eq = buscar_equipo_info(item.get("name"), equipos)
                    if info_eq and "nombre_equipo" in info_eq:
                        puntos_jornada_sel[info_eq["nombre_equipo"]] = item.get("points", 0)

            for n1_cal, n2_cal in partidos_jornada:
                abrev1 = ABREVIATURAS.get(n1_cal, n1_cal[:3].upper())
                abrev2 = ABREVIATURAS.get(n2_cal, n2_cal[:3].upper())
                info1 = buscar_equipo_info(n1_cal, equipos)
                info2 = buscar_equipo_info(n2_cal, equipos)
                esc1 = obtener_ruta_escudo(info1.get("id"), info1.get("escudo_url"))
                esc2 = obtener_ruta_escudo(info2.get("id"), info2.get("escudo_url"))
                
                s1 = esc1 if str(esc1).startswith("http") else (f"data:image/png;base64,{get_image_base64(esc1)}" if get_image_base64(esc1) else "")
                s2 = esc2 if str(esc2).startswith("http") else (f"data:image/png;base64,{get_image_base64(esc2)}" if get_image_base64(esc2) else "")

                if round_closed:
                    g1, g2 = calcular_goles_partido_champions(puntos_jornada_sel.get(normalizar_nombre_equipo(n1_cal), 0), puntos_jornada_sel.get(normalizar_nombre_equipo(n2_cal), 0))
                    centro = f"{g1} - {g2}"
                    estado = "Finalizado"
                else:
                    centro = "VS"
                    estado = "Por comenzar"

                w_h = "30" if st.session_state.get("modo_compacto") else "40"
                font_sz = "0.85rem" if st.session_state.get("modo_compacto") else "1rem"

                st.markdown(f"""
                <div style="background-color: #0b1a40; border: 1px solid rgba(0,163,224,0.4); border-radius: 8px; padding: 12px; margin-bottom: 12px; display: flex; align-items: center; justify-content: space-between; font-size:{font_sz};">
                    <div style="display: flex; align-items: center; gap: 10px;"><img src="{s1}" width="{w_h}" height="{w_h}" style="object-fit:contain;"/><b>{abrev1}</b></div>
                    <div style="text-align: center;"><span style="font-size:0.65rem; color:#8ab4f8;">{estado}</span><div style="background:#050c1f; padding:4px 12px; border-radius:6px; font-weight:900;">{centro}</div></div>
                    <div style="display: flex; align-items: center; gap: 10px;"><b>{abrev2}</b><img src="{s2}" width="{w_h}" height="{w_h}" style="object-fit:contain;"/></div>
                </div>""", unsafe_allow_html=True)

# =========================================================
# 7. SECCIÓN SUPERMANDINGO LEAGUE (INTEGRACIÓN DESDE WEB.PY)
# =========================================================
elif activa == "supermandigo":
    equipos = {}
    rounds_info = []
    jornada_actual = 11
    userteam_id = None

    if email and password:
        token, userid = login_futmondo(email, password)
        if token and userid:
            equipos = obtener_equipos_liga(token, userid, championship_id)
            if equipos:
                userteam_id = next(iter(equipos.values()))["id"]
                rounds_info = obtener_jornadas_usuario(token, userid, championship_id, userteam_id)
                running = [r.get("number") for r in rounds_info if r.get("status") == "running"]
                closed = [r.get("number") for r in rounds_info if r.get("status") == "closed"]
                if running: jornada_actual = running[0]
                elif closed: jornada_actual = min(13, max(closed) + 1)

    round_statuses = {r.get("number"): r.get("status") for r in rounds_info} if rounds_info else {}

    jornada_key_state = "jornada_supermandigo"
    if jornada_key_state not in st.session_state:
        st.session_state[jornada_key_state] = max(1, min(jornada_actual, 13))

    col_tabla, col_partidos = st.columns([1.35, 1], gap="medium")

    with col_tabla:
        st.markdown('<h3 style="color: #ffffff; font-family: \'Montserrat\', sans-serif; font-size: 1.2rem; font-weight: 800; margin-bottom: 10px;">📊 CLASIFICACIÓN</h3>', unsafe_allow_html=True)
            
        if equipos and rounds_info and token and userid:
            modo_movil = st.session_state.get("modo_compacto", False)
            datos_clasificacion, jornadas_jugadas_count = calcular_clasificacion_supermandingo(equipos, rounds_info, token, userid, championship_id, userteam_id)
            st.markdown(render_tabla_clasificacion_supermandingo(datos_clasificacion, max(1, jornadas_jugadas_count), modo_movil=modo_movil), unsafe_allow_html=True)
        else:
            st.warning("Cargando datos reales de SuperMandingo...")

    with col_partidos:
        st.markdown('<h3 style="color: #ffffff; font-family: \'Montserrat\', sans-serif; font-size: 1.2rem; font-weight: 800;">⚽ ENFRENTAMIENTOS</h3>', unsafe_allow_html=True)
        
        jornada_elegida = st.selectbox(
            "Selecciona la Jornada", options=list(range(1, 14)),
            index=st.session_state[jornada_key_state] - 1,
            format_func=lambda x: f"JORNADA {x} — J{MAPEO_LIGA_REAL_SUPERMANDIGO.get(x, x)} de Liga" + (" 🔴 EN JUEGO" if round_statuses.get(x) == "running" else ""),
            key="combo_jornada_selector", label_visibility="collapsed"
        )
        if jornada_elegida != st.session_state[jornada_key_state]:
            st.session_state[jornada_key_state] = jornada_elegida
            st.rerun()

        partidos_jornada = CALENDARIO_JORNADAS_SUPERMANDIGO.get(jornada_elegida, [])
        if partidos_jornada:
            round_obj = next((r for r in rounds_info if r.get("number") == jornada_elegida), None)
            round_status = round_obj.get("status") if round_obj else None
            round_id = round_obj.get("id") if round_obj else None

            puntos_jornada_sel = {}
            if round_id and token and userid:
                for item in obtener_ranking_jornada(token, userid, championship_id, userteam_id, round_id):
                    info_eq = buscar_equipo_info(item.get("name"), equipos)
                    if info_eq and "nombre_equipo" in info_eq:
                        puntos_jornada_sel[info_eq["nombre_equipo"]] = item.get("points", 0)

            team_ids_jornada = []
            for n1_cal, n2_cal in partidos_jornada:
                e1 = buscar_equipo_info(n1_cal, equipos)
                e2 = buscar_equipo_info(n2_cal, equipos)
                if e1 and e1.get("id"): team_ids_jornada.append(e1.get("id"))
                if e2 and e2.get("id"): team_ids_jornada.append(e2.get("id"))

            lineups_cache = {}
            if round_id and token and userid and team_ids_jornada:
                with ThreadPoolExecutor(max_workers=6) as executor:
                    for t_id, l_data in executor.map(lambda tid: (tid, obtener_round_lineup(token, userid, championship_id, round_id, tid)), set(team_ids_jornada)):
                        lineups_cache[t_id] = l_data

            for idx, (nombre1_cal, nombre2_cal) in enumerate(partidos_jornada):
                nombre1 = normalizar_nombre_equipo(nombre1_cal)
                nombre2 = normalizar_nombre_equipo(nombre2_cal)
                abrev1 = ABREVIATURAS.get(nombre1_cal, nombre1[:3].upper())
                abrev2 = ABREVIATURAS.get(nombre2_cal, nombre2[:3].upper())

                eq1_info = buscar_equipo_info(nombre1_cal, equipos)
                eq2_info = buscar_equipo_info(nombre2_cal, equipos)
                escudo1 = obtener_ruta_escudo(eq1_info.get("id"), eq1_info.get("escudo_url"))
                escudo2 = obtener_ruta_escudo(eq2_info.get("id"), eq2_info.get("escudo_url"))

                l1_ans = lineups_cache.get(eq1_info.get("id"), {}) if eq1_info else {}
                l2_ans = lineups_cache.get(eq2_info.get("id"), {}) if eq2_info else {}

                def determinar_estado(r_status, l1, l2):
                    if r_status == "closed": return "Finalizado"
                    p1 = l1.get("players", []) if l1 else []
                    p2 = l2.get("players", []) if l2 else []
                    todos = p1 + p2
                    if not todos: return "En juego" if r_status == "running" else "Por comenzar"
                    puntuados = [p for p in todos if p.get("points", 0) != 0 or p.get("customPoints")]
                    if not puntuados: return "Por comenzar"
                    elif len(puntuados) >= len(todos): return "Finalizado"
                    return "En juego"

                estado_str = determinar_estado(round_status, l1_ans, l2_ans)
                is_closed = round_status == "closed"
                is_running = round_status == "running" or estado_str in ["En juego", "Finalizado"]

                if is_closed or is_running or estado_str != "Por comenzar":
                    pts1 = puntos_jornada_sel.get(nombre1, 0)
                    pts2 = puntos_jornada_sel.get(nombre2, 0)
                    gf1, gf2 = calcular_goles_partido_supermandingo(pts1, pts2, aplicar_regla_diferencia=is_closed)
                    centro_texto = f'<div class="score-box">{gf1} - {gf2}</div>'
                else:
                    centro_texto = f'<div class="score-box" style="font-size: 1.5rem;">VS</div>'

                match_key = f"match_open_{jornada_elegida}_{idx}"
                if match_key not in st.session_state: st.session_state[match_key] = False

                src1 = escudo1 if str(escudo1).startswith("http") else (f"data:image/png;base64,{get_image_base64(escudo1)}" if get_image_base64(escudo1) else "")
                src2 = escudo2 if str(escudo2).startswith("http") else (f"data:image/png;base64,{get_image_base64(escudo2)}" if get_image_base64(escudo2) else "")

                st.markdown(f"""
                <div class="match-container">
                    <div class="match-team"><img src="{src1}" width="50" height="50" style="object-fit:contain;"/><span>{abrev1}</span></div>
                    <div class="match-center"><div style="font-size: 0.74rem; color: #a2b8c2;">{estado_str}</div>{centro_texto}</div>
                    <div class="match-team right"><span>{abrev2}</span><img src="{src2}" width="50" height="50" style="object-fit:contain;"/></div>
                </div>""", unsafe_allow_html=True)

                if is_closed or is_running or estado_str != "Por comenzar":
                    if st.button("▲" if st.session_state[match_key] else "▼", key=f"btn_{match_key}", use_container_width=True):
                        st.session_state[match_key] = not st.session_state[match_key]
                        st.rerun()

                if (is_closed or is_running or estado_str != "Por comenzar") and st.session_state[match_key]:
                    def procesar_alineacion(l_answer):
                        strategy = l_answer.get("strategy") or "1-4-3-3"
                        nums = re.findall(r'\d+', str(strategy))
                        lineas = [int(x) for x in nums[1:]] if len(nums) >= 4 and nums[0] == '1' else ([int(x) for x in nums] if len(nums) == 3 else [4, 3, 3])
                        d_c, m_c, del_c = lineas[0] if len(lineas)>0 else 4, lineas[1] if len(lineas)>1 else 3, lineas[2] if len(lineas)>2 else 3
                        
                        raw = sorted(l_answer.get("players", []), key=lambda x: x.get("position", 99) if isinstance(x.get("position", 99), int) else 99)
                        por, campo = [], []
                        for p in raw:
                            j_obj = {"nombre": formatear_nombre_futmondo(p.get("name") or p.get("playerName")), "puntos": p.get("customPoints") if p.get("customPoints") is not None else p.get("points", 0), "capitan": bool(p.get("cpt") or p.get("captain") or p.get("isCaptain")), "position": p.get("position")}
                            if str(p.get("position")) == "10": por.append(j_obj)
                            else: campo.append(j_obj)
                        
                        delanteros, medios, defensas = campo[:del_c], campo[del_c:del_c+m_c], campo[del_c+m_c:]
                        if len(campo) > del_c + m_c + len(defensas): defensas.extend(campo[del_c+m_c+len(defensas):])
                        return por, [defensas, medios, delanteros]

                    por1, filas1 = procesar_alineacion(l1_ans)
                    por2, filas2 = procesar_alineacion(l2_ans)

                    def construir_fila(juegos):
                        if not juegos: return ""
                        h = '<div class="field-row">'
                        for j in juegos:
                            pts_cl = " player-pts-captain" if j['capitan'] else (" player-pts-zero" if j['puntos'] == 0 else "")
                            h += f'<div class="player-card"><div class="player-name">{j["nombre"]}</div><div class="player-pts{pts_cl}">{j["puntos"]}</div></div>'
                        return h + '</div>'

                    def construir_campo(eq_nombre, esc_url, por_j, filas_j):
                        src = esc_url if str(escudo1).startswith("http") else (f"data:image/png;base64,{get_image_base64(esc_url)}" if get_image_base64(esc_url) else "")
                        img_tag = f"<img src='{src}' width='18' height='18' style='object-fit:contain; vertical-align:middle;'/>" if src else "⚽ "
                        total_pts = sum(j.get('puntos', 0) for j in por_j + [f for fila in filas_j for f in fila])
                        filas_html = "".join([construir_fila(f) for f in reversed(filas_j)]) + construir_fila(por_j)
                        return f'<div style="flex: 1; min-width: 0;"><div class="soccer-field"><div class="field-header-top-left">{img_tag}<span style="color: #ffffff; font-weight: 800; font-size: 0.8rem;">{eq_nombre.upper()}</span></div><div class="field-header-top-right">{total_pts} pts</div><div class="field-line-center"></div>{filas_html}</div></div>'

                    st.markdown(f'<div class="lineup-unified-card"><div class="fields-flex-container">{construir_campo(nombre1, escudo1, por1, filas1)}{construir_campo(nombre2, escudo2, por2, filas2)}</div></div>', unsafe_allow_html=True)
        else:
            st.warning("No hay enfrentamientos programados para esta jornada.")

else:
    st.markdown(
        """
        <div style="text-align: center; padding: 60px 20px; font-family: 'Montserrat', sans-serif;">
            <h3 style="color: #8ab4f8; font-weight: 800; margin-bottom: 10px;">Información no disponible en estos momentos</h3>
            <p style="color: #aaaaaa; font-size: 0.95rem;">Próximamente habilitaremos los datos para esta competición.</p>
        </div>
        """,
        unsafe_allow_html=True
    )
