import streamlit as st
import io
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from num2words import num2words

st.set_page_config(page_title="Foliador UIE", layout="centered")

st.title("📄 Foliador UIE")
st.write("Configura cuándo y cómo empieza la numeración en el panel de la izquierda.")

# --- PANEL LATERAL (CONFIGURACIÓN) ---
with st.sidebar:
    st.header("1. Configuración de Números")
    # El número que se escribirá físicamente (ej: 5. Cinco)
    numero_a_escribir = st.number_input("¿Con qué número empezar?", value=1, min_value=0)
    
    # La página del documento donde aparece el primer número
    pagina_donde_empieza = st.number_input("¿En qué página del PDF empezar a mostrar números?", value=1, min_value=1)

    st.header("2. Diseño")
    font_size = st.slider("Tamaño de letra", 8, 24, 12)
    margen_superior = st.slider("Margen superior (pulgadas)", 0.1, 2.0, 0.5)

archivo_subido = st.file_uploader("Sube tu archivo PDF", type="pdf")

if archivo_subido:
    if st.button("🚀 Procesar PDF"):
        try:
            with st.spinner("Generando numeración..."):
                reader = PdfReader(archivo_subido)
                writer = PdfWriter()
                
                # Procesamos cada página del PDF original
                for i in range(len(reader.pages)):
                    page = reader.pages[i]
                    
                    # Detectar tamaño real de la página
                    width = float(page.mediabox.width)
                    height = float(page.mediabox.height)
                    
                    # Creamos la capa transparente (overlay)
                    packet = io.BytesIO()
                    can = canvas.Canvas(packet, pagesize=(width, height))
                    
                    # --- LÓGICA DE ACTIVACIÓN ---
                    # i es el índice (empieza en 0), por eso usamos i + 1 para "página humana"
                    numero_pagina_actual = i + 1
                    
                    if numero_pagina_actual >= pagina_donde_empieza:
                        # Calculamos el número que corresponde escribir
                        # Es el número inicial + la diferencia de páginas procesadas
                        conteo_actual = numero_a_escribir + (numero_pagina_actual - pagina_donde_empieza)
                        
                        word = num2words(conteo_actual, lang='es').capitalize()
                        text = f"{conteo_actual}. {word}"
                        
                        can.setFont("Courier-Bold", font_size)
                        # Dibujamos en el centro superior
                        can.drawCentredString(width / 2, height - (margen_superior * inch), text)
                    
                    can.showPage()
                    can.save()
                    
                    packet.seek(0)
                    overlay_reader = PdfReader(packet)
                    overlay_page = overlay_reader.pages[0]
                    
                    # Fusionamos la capa de texto con la página original
                    page.merge_page(overlay_page)
                    writer.add_page(page)
                
                # Preparar el archivo final para descarga
                output = io.BytesIO()
                writer.write(output)
                output.seek(0)
                
                st.success("✅ ¡PDF procesado!")
                st.download_button(
                    label="📥 Descargar PDF Numerado",
                    data=output,
                    file_name="pdf_numerado.pdf",
                    mime="application/pdf"
                )
        except Exception as e:
            st.error(f"Hubo un error: {e}")
