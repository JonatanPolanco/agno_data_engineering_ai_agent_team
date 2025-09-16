import streamlit as st
import uuid
from datetime import datetime
from src.core.team_builder import build_team

st.set_page_config(
    page_title="Agno AI Data Engineering Agents", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# 🔧 Inicialización segura
# =========================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "user" not in st.session_state:
    st.session_state.user = ""

if "session_id" not in st.session_state:
    st.session_state.session_id = None

if "team" not in st.session_state:
    st.session_state.team = None

if "conversation_count" not in st.session_state:
    st.session_state.conversation_count = 0

# =========================
# ⚙️ Sidebar: configuración
# =========================
st.sidebar.title("⚙️ Configuración")

# Input de usuario
user_input = st.sidebar.text_input("👤 Ingresa tu nombre de usuario:", st.session_state.user)
if user_input != st.session_state.user:
    st.session_state.user = user_input

# Generar session_id si no existe y ya tenemos usuario
if not st.session_state.session_id and st.session_state.user:
    st.session_state.session_id = f"{st.session_state.user}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"

# Información de sesión
if st.session_state.user and st.session_state.session_id:
    st.sidebar.info(f"🆔 **Sesión**: `{st.session_state.session_id}`")
    st.sidebar.info(f"💬 **Conversaciones**: {st.session_state.conversation_count}")

# Controles de sesión
col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button("🆕 Nueva sesión"):
        if st.session_state.user:
            st.session_state.session_id = f"{st.session_state.user}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
            st.session_state.messages = []
            st.session_state.conversation_count = 0
            st.session_state.team = None  # Forzar recreación del team
            st.success("✅ Nueva sesión creada")
            st.rerun()
        else:
            st.sidebar.warning("Debes ingresar un usuario primero.")

with col2:
    if st.button("🗑️ Limpiar chat"):
        st.session_state.messages = []
        st.session_state.conversation_count = 0
        st.success("🗑️ Chat limpiado")
        st.rerun()

# Separador
st.sidebar.markdown("---")

# Debug mode
debug_mode = st.sidebar.checkbox("🔍 Debug mode")

if debug_mode:
    st.sidebar.json({
        "user": st.session_state.user,
        "session_id": st.session_state.session_id,
        "messages_count": len(st.session_state.messages),
        "team_initialized": st.session_state.team is not None
    })

# Información del sistema
st.sidebar.markdown("### ℹ️ Agentes Disponibles")
st.sidebar.markdown("""
- 🤖 **RAG Agent**: Conocimiento interno
- 🌐 **Web Agent**: Documentación oficial  
- 💻 **Code Standards**: Generación de código
""")

# =========================
# 💬 Chat UI principal
# =========================
st.title("🤖 Agno AI Data Engineering Agents")

if not st.session_state.user:
    st.warning("👆 **Ingresa tu nombre de usuario en la barra lateral para comenzar.**")
    st.markdown("""
    ### 🚀 Sistema Multi-Agente para Ingeniería de Datos
    
    Este sistema te ayuda con:
    - 📚 **Consultas técnicas** basadas en conocimiento curado
    - 🌐 **Documentación actualizada** de tecnologías oficiales
    - 💻 **Generación de código** con estándares enterprise
    - 🎯 **Recomendaciones arquitecturales** para sistemas de datos
    
    **Para empezar**: Ingresa tu nombre de usuario en la barra lateral.
    """)
else:
    # Crear equipo si aún no existe
    if st.session_state.team is None:
        try:
            with st.spinner("🤖 Inicializando equipo de agentes..."):
                st.session_state.team = build_team(
                    user=st.session_state.user,
                    session_id=st.session_state.session_id,
                )
            st.success("✅ Equipo de agentes inicializado correctamente")
        except Exception as e:
            st.error(f"❌ Error al inicializar el equipo: {e}")
            st.stop()

    # Mostrar historial de mensajes
    for i, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Mostrar metadatos en debug mode
            if debug_mode and "metadata" in message:
                with st.expander("🔍 Debug info"):
                    st.json(message["metadata"])

    # Input del usuario - ESTA ES LA PARTE QUE FALTABA
    if prompt := st.chat_input("💬 Escribe tu consulta sobre ingeniería de datos..."):
        # Agregar mensaje del usuario
        st.session_state.messages.append({
            "role": "user", 
            "content": prompt,
            "timestamp": datetime.now().isoformat()
        })
        
        # Mostrar mensaje del usuario
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Procesar con el equipo de agentes
        with st.chat_message("assistant"):
            with st.spinner("🤖 Consultando con el equipo de agentes..."):
                try:
                    # Ejecutar consulta
                    response = st.session_state.team.run(prompt)
                    
                    # Extraer contenido de respuesta
                    response_content = getattr(response, "content", str(response))
                    
                    # Mostrar respuesta
                    st.markdown(response_content)
                    
                    # Agregar a historial
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response_content,
                        "timestamp": datetime.now().isoformat(),
                        "metadata": {
                            "conversation_number": st.session_state.conversation_count + 1,
                            "session_id": st.session_state.session_id
                        }
                    })
                    
                    # Incrementar contador
                    st.session_state.conversation_count += 1
                    
                    # Mostrar sugerencia cada 3 consultas
                    if st.session_state.conversation_count % 3 == 0:
                        st.info("💡 **Tip**: Puedes usar 'Limpiar chat' para reiniciar el contexto o 'Nueva sesión' para empezar desde cero.")
                    
                except Exception as e:
                    error_msg = f"❌ **Error al procesar la consulta**: {e}"
                    st.error(error_msg)
                    
                    # Agregar error al historial
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg,
                        "timestamp": datetime.now().isoformat(),
                        "metadata": {"error": str(e)}
                    })
                    
                    # Sugerencias de troubleshooting
                    with st.expander("🔧 Posibles soluciones"):
                        st.markdown("""
                        - **Conexión**: Verifica tu conexión a internet
                        - **Configuración**: Revisa las variables de entorno de Google Cloud
                        - **Permisos**: Asegúrate de tener los permisos correctos en Vertex AI
                        - **Consulta**: Intenta reformular tu pregunta
                        """)

# =========================
# 📊 Footer con información
# =========================
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    if st.session_state.user:
        st.metric("👤 Usuario", st.session_state.user)

with col2:
    if st.session_state.session_id:
        st.metric("💬 Conversaciones", st.session_state.conversation_count)

with col3:
    if st.session_state.team:
        st.metric("🤖 Estado", "🟢 Activo")
    else:
        st.metric("🤖 Estado", "🔴 Inactivo")