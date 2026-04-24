import streamlit as st
import io
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from num2words import num2words

# Configuración básica de la página
st.set_page_config(page_title="Foliador UIE", layout="centered")

st.title("📄 Foliador UIE 📄")
st.write("Configura el inicio de la numeración y sube tu archivo.")

# --- VALORES PREDETERMINADOS (FIJOS) ---
FONT_SIZE = 12
MARGEN_SUPERIOR = 0.5

# --- PANEL LATERAL (CONFIGURACIÓN + FAQ) ---
with st.sidebar:
    st.header("⚙️ Configuración")
    numero_a_escribir = st.number_input("¿Con qué número empezar?", value=1, min_value=0)
    pagina_donde_empieza = st.number_input("¿En qué página del PDF empezar?", value=1, min_value=1)
    
    st.divider() # Línea divisoria

    # --- SECCIÓN DE FAQ ---
    st.subheader("❓ Preguntas Frecuentes")
    
    with st.expander("¿Qué hace esta app?"):
        st.write("""
            Esta herramienta agrega números de página en formato **'1. Uno'** centrados en la parte superior. Está optimizada para hojas tamaño 
            **Oficio (8.3\" x 13\")**.
        """)

    with st.expander("¿Puedo saltarme la portada?"):
        st.write("""
            ¡Sí! En la casilla **'¿En qué página del PDF empezar?'**, pon el 
            número de página donde quieres que aparezca el primer número. 
            Las páginas anteriores quedarán en blanco.
        """)

    with st.expander("¿Qué pasa si mi PDF no es Oficio?"):
        st.write("""
            La app detecta el tamaño de cada página automáticamente. Si tu PDF es 
            Carta o A4, el número se centrará igual, pero el margen de 0.5\" 
            se calculará según el tamaño de esa hoja.
        """)

    with st.expander("¿Mis archivos están seguros?"):
        st.write("""
            Sí. Los archivos se procesan en la memoria del servidor y se borran 
            automáticamente al cerrar la sesión. No se guardan de forma permanente.
        """)

    with st.expander("No veo los números, ¿qué hago?"):
        st.write("""
            Si el PDF es un escaneo muy oscuro o tiene márgenes físicos muy grandes, 
            el número podría quedar oculto. Asegúrate de que el PDF original 
            tenga espacio libre en el borde superior.
        """)

if archivo_subido:
    if st.button("🚀 Generar Numeración"):
        try:
            with st.spinner("Procesando..."):
                reader = PdfReader(archivo_subido)
                writer = PdfWriter()
                
                for i in range(len(reader.pages)):
                    page = reader.pages[i]
                    
                    # Detectar tamaño real de la página
                    width = float(page.mediabox.width)
                    height = float(page.mediabox.height)
                    
                    # Crear capa transparente
                    packet = io.BytesIO()
                    can = canvas.Canvas(packet, pagesize=(width, height))
                    
                    # Lógica de activación (i+1 es la página actual)
                    numero_pagina_actual = i + 1
                    
                    if numero_pagina_actual >= pagina_donde_empieza:
                        # Cálculo del número correlativo
                        conteo_actual = numero_a_escribir + (numero_pagina_actual - pagina_donde_empieza)
                        
                        # Conversión a palabras en español
                        word = num2words(conteo_actual, lang='es').capitalize()
                        text = f"{conteo_actual}. {word}"
                        
                        # Aplicar valores predeterminados
                        can.setFont("Courier-Bold", FONT_SIZE)
                        can.drawCentredString(width / 2, height - (MARGEN_SUPERIOR * inch), text)
                    
                    can.showPage()
                    can.save()
                    
                    packet.seek(0)
                    overlay_reader = PdfReader(packet)
                    overlay_page = overlay_reader.pages[0]
                    
                    # Fusionar capas
                    page.merge_page(overlay_page)
                    writer.add_page(page)
                
                # Preparar descarga
                output = io.BytesIO()
                writer.write(output)
                output.seek(0)
                
                st.success("✅ ¡PDF listo para descargar!")
                st.download_button(
                    label="📥 Descargar ahora",
                    data=output,
                    file_name="archivo_numerado.pdf",
                    mime="application/pdf"
                )
        except Exception as e:
            st.error(f"Error al procesar: {e}")
