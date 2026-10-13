import os, sqlite3, uuid
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import quote
import streamlit as st

ROOT = Path(__file__).resolve().parent
DB = ROOT / "sakura.db"
AUDIO_DIR = ROOT / "sakura_audio"
AUDIO_DIR.mkdir(exist_ok=True)
KINDS = ["Tarea", "Meta", "Recordatorio", "Nota", "Frase motivacional"]
MOODS = ["🌧️ Muy bajita", "🌥️ Bajita", "⛅ Neutral", "🌤️ Bien", "☀️ Radiante"]
ENERGIES = ["🔴 Baja", "🟡 Media", "🟢 Alta"]

def db():
    c = sqlite3.connect(DB, check_same_thread=False)
    c.row_factory = sqlite3.Row
    return c

def query(sql, args=()):
    with db() as c:
        return [dict(r) for r in c.execute(sql, args).fetchall()]

def run(sql, args=()):
    with db() as c:
        c.execute(sql, args)
        c.commit()

def init():
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS categories(id TEXT PRIMARY KEY,name TEXT UNIQUE NOT NULL,emoji TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS items(id TEXT PRIMARY KEY,title TEXT NOT NULL,category_id TEXT,kind TEXT NOT NULL,
          details TEXT DEFAULT '',status TEXT DEFAULT 'open',created_at TEXT NOT NULL,due_date TEXT,audio_path TEXT,
          postponed INTEGER DEFAULT 0,completed_at TEXT,FOREIGN KEY(category_id) REFERENCES categories(id));
        CREATE TABLE IF NOT EXISTS checkins(day TEXT PRIMARY KEY,mood TEXT,energy TEXT,note TEXT DEFAULT '');
        CREATE TABLE IF NOT EXISTS cycle_logs(day TEXT PRIMARY KEY,period INTEGER,symptoms TEXT,note TEXT);
        """)
        if c.execute("SELECT COUNT(*) FROM categories").fetchone()[0] == 0:
            for emoji, name in [("💼","Trabajo"),("🏡","Casa"),("🫶","Amigas"),("🛼","Patinaje"),("🌸","Yo y bienestar"),("🎨","Creatividad")]:
                c.execute("INSERT INTO categories VALUES(?,?,?)", (str(uuid.uuid4()), name, emoji))

def add_item(title, cat=None, kind="Nota", details="", due=None, audio=None):
    run("INSERT INTO items(id,title,category_id,kind,details,status,created_at,due_date,audio_path) VALUES(?,?,?,?,?,'open',?,?,?)",
        (str(uuid.uuid4()), title.strip(), cat, kind, details.strip(), datetime.now().isoformat(timespec="seconds"), str(due) if due else None, audio))

def share_url(item):
    msg = "🌸 Santuario Sakura\n" + item["title"]
    if item.get("details"): msg += "\n" + item["details"]
    if item.get("due_date"): msg += "\nFecha: " + item["due_date"]
    return "https://wa.me/?text=" + quote(msg)

def gcal_url(item):
    title = quote(item["title"])
    details = quote(item.get("details", "") + "\n(Generado desde Santuario Sakura 🌸)")
    dates_str = ""
    if item.get("due_date"):
        d = item["due_date"].replace("-", "")
        dates_str = f"&dates={d}/{d}"
    return f"https://calendar.google.com/calendar/render?action=TEMPLATE&text={title}&details={details}{dates_str}"

def css():
    st.markdown("""<style>
    .stApp{background:radial-gradient(ellipse at top,#25243b 0%,#10121c 48%,#090b12 100%);color:#f6edf4}
    [data-testid="stSidebar"]{background:#111522;border-right:1px solid #40344e}
    h1,h2,h3{color:#fff0f7!important;letter-spacing:-.02em}
    div.stButton>button{width:100%;min-height:3rem;border-radius:15px;border:1px solid #59435d;background:#26243a;color:#fff2f7;font-weight:600}
    div.stButton>button:hover{background:#3a2a40;border-color:#f2a8c6;color:white}
    div[data-testid="stMetric"]{background:#222236;border:1px solid #40364e;padding:12px;border-radius:16px}
    [data-testid="stForm"]{border:1px solid #40364e;border-radius:16px;padding:1rem;background:#171927}
    .sub{color:#d9b5c7}
    </style>""", unsafe_allow_html=True)

st.set_page_config(page_title="Santuario Sakura", page_icon="🌸", layout="centered")
init(); css()

if "page" not in st.session_state: st.session_state.page = "Inicio"
if "cat" not in st.session_state: st.session_state.cat = None

with st.sidebar:
    st.markdown("## 🌸 Santuario")
    page = st.radio("Ir a", ["Inicio","Inbox del viento","Mi jardín","Ajustes"],
                    index=["Inicio","Inbox del viento","Mi jardín","Ajustes"].index(st.session_state.page)
                    if st.session_state.page in ["Inicio","Inbox del viento","Mi jardín","Ajustes"] else 0)
    if page != st.session_state.page:
        st.session_state.page = page; st.session_state.cat = None; st.rerun()
    st.caption("Tu ritmo también cuenta. 🌙")

st.markdown("# 🌸 Santuario Sakura")
st.markdown('<p class="sub">Pequeños pasos, espacio para respirar y cero culpa.</p>', unsafe_allow_html=True)

total_hechos = query("SELECT COUNT(*) n FROM items WHERE status='done'")[0]["n"]

# Configuración de niveles e imágenes de Okami
if total_hechos < 4:
    nivel_okami = "🐾 Nivel 1: Cachorro de los Cerezos"
    desc_okami = "Un pequeño paso. El viaje recién comienza bajo los brotes de sakura."
    foto_okami = ROOT / "okami_1.png"
elif total_hechos < 10:
    nivel_okami = "🌸 Nivel 2: Guardián de los Pétalos"
    desc_okami = "Tu constancia alimenta el santuario. ¡Los pétalos giran a tu favor!"
    foto_okami = ROOT / "okami_2.png"
elif total_hechos < 20:
    nivel_okami = "⚔️ Nivel 3: Guerrero del Alba"
    desc_okami = "¡Magia pura! Tu energía está transformando tu espacio con armonía."
    foto_okami = ROOT / "okami_3.png"
else:
    nivel_okami = "✨ Nivel 4: Espíritu Protector Legendario"
    desc_okami = "Has alcanzado la maestría de tu refugio. ¡Okami brilla con todo su poder!"
    foto_okami = ROOT / "okami_4.png"

# Mostrar tarjeta con la imagen de Okami en la nube sin problemas
st.markdown(f"""
    <div style="background:linear-gradient(145deg,#2f2842,#191924);border:2px solid #ffb7c5;border-radius:20px;padding:20px;text-align:center;margin-bottom:20px;">
        <h3 style="color: #ffb7c5; margin-bottom: 8px; font-size: 1.3em;">{nivel_okami}</h3>
        <p style="color: #f6edf4; font-size: 0.95em; margin: 0;">{desc_okami}</p>
        <p style="color: #d9b5c7; font-size: 0.8em; margin-top: 10px;">Metas liberadas: <b>{total_hechos}</b></p>
    </div>
""", unsafe_allow_html=True)

if foto_okami.exists():
    st.image(str(foto_okami), use_container_width=True)

with st.expander("🌅 Semáforo de energía (opcional)"):
    with st.form("checkin"):
        mood = st.select_slider("¿Cómo está tu ánimo?", options=MOODS, value="⛅ Neutral")
        energy = st.radio("Energía", ENERGIES, horizontal=True)
        note = st.text_input("¿Qué necesitas recordar hoy?", placeholder="Hoy necesito…")
        if st.form_submit_button("Guardar check-in", use_container_width=True):
            run("""INSERT INTO checkins VALUES(?,?,?,?) ON CONFLICT(day) DO UPDATE SET mood=excluded.mood,energy=excluded.energy,note=excluded.note""",
                (date.today().isoformat(), mood, energy, note))
            st.success("Guardado. No necesitas rendir igual todos los días."); st.rerun()

def categories():
    return query("SELECT * FROM categories ORDER BY name COLLATE NOCASE")

def inbox_items():
    return query("SELECT * FROM items WHERE category_id IS NULL AND status='open' ORDER BY created_at DESC")

if st.session_state.page == "Inicio":
    st.markdown("## ¿Dónde quieres poner tu atención?")
    st.write("Elige un pequeño rincón. No tienes que resolverlo todo ahora.")
    cats = categories()
    with st.expander("＋ Crear una categoría"):
        with st.form("newcat"):
            name = st.text_input("Nombre", placeholder="Ej. Estudios, Finanzas, Viajes")
            emoji = st.selectbox("Símbolo", ["🌸","💼","🏡","🫶","🛼","🎨","📚","🌱","💌","🧠","✨","🧺"])
            if st.form_submit_button("Crear categoría", use_container_width=True):
                if not name.strip(): st.warning("Escribe un nombre.")
                elif any(c["name"].lower()==name.strip().lower() for c in cats): st.warning("Esa categoría ya existe.")
                else:
                    run("INSERT INTO categories VALUES(?,?,?)", (str(uuid.uuid4()),name.strip(),emoji)); st.rerun()
    for n in range(0,len(cats),2):
        cols=st.columns(2)
        for col,cat in zip(cols,cats[n:n+2]):
            count=query("SELECT COUNT(*) n FROM items WHERE category_id=? AND status='open'",(cat["id"],))[0]["n"]
            with col:
                if st.button(f"{cat['emoji']}  {cat['name']}\n{count} pendientes",key=cat["id"]):
                    st.session_state.cat=cat["id"]; st.session_state.page="Categoría"; st.rerun()
    a,b=st.columns(2)
    with a:
        if st.button(f"🍃 Inbox del viento · {len(inbox_items())}"): st.session_state.page="Inbox del viento"; st.rerun()
    with b:
        if st.button("🌙 Mi jardín de progreso"): st.session_state.page="Mi jardín"; st.rerun()

elif st.session_state.page == "Inbox del viento":
    st.markdown("## 🍃 Inbox del viento")
    st.write("Captura primero; clasifica después.")
    with st.form("quicknote"):
        title=st.text_area("Idea rápida",placeholder="Escribe como te salga…",height=100)
        details=st.text_input("Detalle opcional")
        if st.form_submit_button("Guardar sin clasificar",use_container_width=True):
            if title.strip(): add_item(title,kind="Nota",details=details); st.rerun()
            else: st.warning("Escribe algo antes de guardar.")
    st.markdown("### 🎙️ Nota de voz")
    audio=st.audio_input("Graba una nota")
    if audio is not None:
        st.audio(audio)
        if st.button("Guardar audio",use_container_width=True):
            raw=audio.getvalue(); filename=f"{uuid.uuid4()}.wav"; path=AUDIO_DIR/filename; path.write_bytes(raw)
            add_item("Nota de voz grabada",kind="Nota",details="Audio guardado localmente.",audio=str(path))
            st.success("Audio guardado en tu Inbox con éxito.")
            st.rerun()
    cats=categories()
    for item in inbox_items():
        with st.container(border=True):
            st.markdown(f"**{item['title']}**")
            if item["details"]: st.caption(item["details"])
            if item["audio_path"] and Path(item["audio_path"]).exists(): st.audio(Path(item["audio_path"]).read_bytes())
            
            choices=["Inbox (sin clasificar)"]+[c["name"] for c in cats]
            current_cat_name = "Inbox (sin clasificar)"
            if item["category_id"]:
                found_cat = next((c for c in cats if c["id"] == item["category_id"]), None)
                if found_cat: current_cat_name = found_cat["name"]
            
            dest = st.selectbox("Categoría", choices, index=choices.index(current_cat_name), key="dest_"+item["id"])
            kind = st.selectbox("Tipo", KINDS, index=KINDS.index(item["kind"]) if item["kind"] in KINDS else 3, key="kind_"+item["id"])
            
            col_1, col_2 = st.columns(2)
            with col_1:
                if st.button("Guardar cambios", key="save_"+item["id"]):
                    cid = next((c["id"] for c in cats if c["name"] == dest), None)
                    run("UPDATE items SET category_id=?, kind=? WHERE id=?", (cid, kind, item["id"]))
                    st.success("¡Clasificado con éxito!")
                    st.rerun()
            with col_2:
                if st.button("Eliminar", key="delete_"+item["id"]):
                    run("DELETE FROM items WHERE id=?", (item["id"],))
                    st.rerun()
            
            st.link_button("📲 Preparar mensaje para WhatsApp", share_url(item), use_container_width=True)
            st.link_button("📅 Añadir a Google Calendar", gcal_url(item), use_container_width=True)

elif st.session_state.page == "Categoría":
    cats=categories(); cat=next((c for c in cats if c["id"]==st.session_state.cat),None)
    if not cat:
        st.warning("Categoría no encontrada.")
        if st.button("Volver"): st.session_state.page="Inicio"; st.rerun()
    else:
        if st.button("← Todas las categorías"): st.session_state.page="Inicio"; st.rerun()
        st.markdown(f"## {cat['emoji']} {cat['name']}")
        view=st.radio("Cómo quieres verlo",["Ver todo agrupado","Tarjetas mágicas"],horizontal=True)
        with st.expander("＋ Añadir algo aquí (Cumpleaños, Reuniones, etc.)"):
            with st.form("addcatitem"):
                title=st.text_area("Qué quieres recordar (Ej. Cumpleaños de mamá, Reunión de trabajo)")
                kind=st.selectbox("Tipo",KINDS, index=2)
                details=st.text_input("Detalle opcional")
                due=st.date_input("Fecha",value=date.today(),format="DD/MM/YYYY")
                if st.form_submit_button("Guardar",use_container_width=True):
                    if title.strip(): add_item(title,cat["id"],kind,details,due); st.rerun()
                    else: st.warning("Escribe algo primero.")
        items=query("""SELECT * FROM items WHERE category_id=? AND status='open'
          ORDER BY CASE kind WHEN 'Meta' THEN 1 WHEN 'Tarea' THEN 2 WHEN 'Recordatorio' THEN 3 ELSE 4 END,created_at DESC""",(cat["id"],))
        if view=="Ver todo agrupado":
            for kind in KINDS:
                group=[i for i in items if i["kind"]==kind]
                if group:
                    st.markdown(f"### {kind}")
                    for item in group:
                        with st.container(border=True):
                            st.markdown(f"**{item['title']}**")
                            if item["details"]: st.caption(item["details"])
                            if item["due_date"]: st.caption("📅 "+item["due_date"])
                            a,b,c=st.columns(3)
                            with a:
                                if st.button("Hecho ❤️",key="done"+item["id"]): 
                                    run("UPDATE items SET status='done',completed_at=? WHERE id=?",(datetime.now().isoformat(),item["id"]))
                                    st.balloons()
                                    st.rerun()
                            with b:
                                if st.button("Posponer 🌙",key="post"+item["id"]): run("UPDATE items SET postponed=postponed+1,due_date=? WHERE id=?",((date.today()+timedelta(days=1)).isoformat(),item["id"])); st.toast("Lo dejamos para mañana, sin culpa."); st.rerun()
                            with c: st.link_button("📲 Enviar",share_url(item))
                            st.link_button("📅 Añadir a Google Calendar", gcal_url(item), use_container_width=True)
            if not items: st.info("Este rincón está tranquilo. Puedes añadir algo o dejarlo así.")
        else:
            cards=[i for i in items if i["kind"] in ["Meta","Tarea","Recordatorio"]]
            if not cards: st.info("No hay metas ni tareas pendientes. Puedes descansar o añadir una cuando quieras.")
            else:
                if "magic" not in st.session_state: st.session_state.magic=0
                idx=st.session_state.magic % len(cards); item=cards[idx]
                st.markdown(f"""<div style="background:linear-gradient(145deg,#29263e,#171827);border:1px solid #61465e;border-radius:22px;padding:1.4rem">
                <small>Tarjeta {idx+1} de {len(cards)} · {item['kind']}</small><h2>{item['title']}</h2>
                <p>{item['details']}</p><p>Fecha: {item.get('due_date', 'Sin fecha')} 🌸</p></div>""",unsafe_allow_html=True)
                a,b=st.columns(2)
                with a:
                    if st.button("¡Hecho! ❤️",key="magicdone",use_container_width=True):
                        run("UPDATE items SET status='done',completed_at=? WHERE id=?",(datetime.now().isoformat(),item["id"]))
                        st.session_state.magic=0
                        st.balloons()
                        st.toast("¡Un paso más! Okami ha ganado energía. 🐾")
                        st.rerun()
                with b:
                    if st.button("Posponer 🌙",key="magicpost",use_container_width=True):
                        run("UPDATE items SET postponed=postponed+1,due_date=? WHERE id=?",((date.today()+timedelta(days=1)).isoformat(),item["id"])); st.session_state.magic=(idx+1)%len(cards); st.toast("Posponer también es elegir."); st.rerun()
                if len(cards)>1 and st.button("Ver siguiente →"):
                    st.session_state.magic=(idx+1)%len(cards); st.rerun()
                st.link_button("📲 Preparar mensaje para WhatsApp",share_url(item),use_container_width=True)
                st.link_button("📅 Añadir a Google Calendar", gcal_url(item), use_container_width=True)

elif st.session_state.page == "Mi jardín":
    st.markdown("## 🌙 Mi jardín de progreso")
    items=query("SELECT * FROM items")
    done=[i for i in items if i["status"]=="done"]
    open_items=[i for i in items if i["status"]=="open"]
    total=sum(i["kind"] in ["Meta","Tarea"] for i in items)
    completed=sum(i["kind"] in ["Meta","Tarea"] for i in done)
    pct=round(completed/total*100) if total else 0
    a,b,c=st.columns(3); a.metric("Completados",len(done)); b.metric("Pendientes",len(open_items)); c.metric("Avance",f"{pct}%")
    st.progress(pct/100 if total else 0)
    st.caption("Un indicador, no una calificación de tu valor.")
    st.markdown("### 🌦️ Ánimo y energía")
    checkins=query("SELECT * FROM checkins ORDER BY day")
    if checkins:
        for ch in checkins:
            st.markdown(f"- **{ch['day']}** | Ánimo: {ch['mood']} | Energía: {ch['energy']} | Nota: {ch['note']}")
    else: st.info("Puedes registrar tu ánimo desde el semáforo cuando te sirva.")
    st.markdown("### 🌸 Ciclo y autocuidado")
    with st.form("cycle"):
        day=st.date_input("Día observado",value=date.today(),format="DD/MM/YYYY")
        period=st.checkbox("Estoy menstruando hoy")
        symptoms=st.text_input("Observaciones (síntomas)")
        need=st.text_input("¿Qué te ayudaría hoy?")
        if st.form_submit_button("Guardar observación",use_container_width=True):
            run("""INSERT INTO cycle_logs VALUES(?,?,?,?) ON CONFLICT(day) DO UPDATE SET period=excluded.period,symptoms=excluded.symptoms,note=excluded.note""",
                (day.isoformat(),int(period),symptoms,need)); st.success("Observación guardada."); st.rerun()

elif st.session_state.page == "Ajustes":
    st.markdown("## ⚙️ Ajustes y privacidad")
    st.write("Los datos se guardan localmente en `sakura.db`; los audios, en `sakura_audio/`.")
    st.warning("Protege tu equipo; los datos son completamente locales y privados.")

st.markdown("---")
st.markdown('<p style="text-align:center;color:#bdb3c7">Hecho con calma · Un pétalo a la vez 🌸</p>',unsafe_allow_html=True)