import streamlit as st
import io
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import red, black # Para pruebas
from num2words import num2words

st.set_page_config(page_title="Foliador UIE", layout="centered")

st.title("📄 Foliador de Expedientes")
st.write("Esta es la nueva versión del Foliador")

# Panel lateral
with st.sidebar:
    st.header("Configuración")
    numero_inicial = st.number_input("Número de inicio", value=1, min_value=0)
    font_size = st.slider("Tamaño de letra", 8, 30, 14)
    margen_puntos = st.slider("Distancia desde el borde superior", 10, 100, 30)
    
archivo_subido = st.file_uploader("Sube tu PDF aquí", type="pdf")

if archivo_subido:
    if st.button("🔢 Generar Numeración"):
        try:
            with st.spinner("Procesando..."):
                reader = PdfReader(archivo_subido)
                writer = PdfWriter()
                
                # Procesar cada página individualmente
                for i in range(len(reader.pages)):
                    page = reader.pages[i]
                    
                    # --- DETECTAR TAMAÑO REAL DE LA PÁGINA ---
                    # Esto lee el tamaño interno del PDF (en puntos)
                    width = float(page.mediabox.width)
                    height = float(page.mediabox.height)
                    
                    # Crear overlay para ESTA página específica
                    packet = io.BytesIO()
                    can = canvas.Canvas(packet, pagesize=(width, height))
                    
                    # Lógica de texto
                    current_num = numero_inicial + i
                    word = num2words(current_num, lang='es').capitalize()
                    text = f"{current_num}. {word}"
                    
                    # Configurar Fuente y Color
                    can.setFont("Courier-Bold", font_size)
                    can.setFillColor(black)
                    
                    # Dibujar en el centro superior relativo a la página
                    can.drawCentredString(width / 2, height - margen_puntos, text)
                    can.showPage()
                    can.save()
                    
                    packet.seek(0)
                    overlay_page = PdfReader(packet).pages[0]
                    
                    # Fusionar: El overlay se pone ENCIMA de la página original
                    page.merge_page(overlay_page)
                    writer.add_page(page)
                
                # Preparar descarga
                output = io.BytesIO()
                writer.write(output)
                output.seek(0)
                
                st.success("¡Numeración completada!")
                st.download_button(
                    label="📥 Descargar PDF",
                    data=output,
                    file_name="archivo_numerado.pdf",
                    mime="application/pdf"
                )
        except Exception as e:
            st.error(f"Ocurrió un error técnico: {e}")
