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

# --- PANEL LATERAL (CONFIGURACIÓN SIMPLIFICADA) ---
with st.sidebar:
    st.header("Configuración")
    # El número que se escribirá físicamente
    numero_a_escribir = st.number_input("¿Con qué número empezar?", value=1, min_value=0)
    
    # La página del documento donde aparece el primer número
    pagina_donde_empieza = st.number_input("¿En qué página del PDF empezar?", value=1, min_value=1)

archivo_subido = st.file_uploader("Sube tu archivo PDF", type="pdf")

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
