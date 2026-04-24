import streamlit as st
import io
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from num2words import num2words

# Configuración de la página
st.set_page_config(page_title="Numerador de Oficio", page_icon="📄")
st.title("📄 Numerador de PDFs (Formato Oficio)")

# Barra lateral con opciones
st.sidebar.header("Configuración")
archivo_subido = st.file_uploader("Sube tu archivo PDF", type="pdf")
numero_inicial = st.sidebar.number_input("Número de inicio", value=1, min_value=0)
tamaño_fuente = st.sidebar.slider("Tamaño de letra", 8, 20, 12)
margen_superior = st.sidebar.slider("Margen superior (pulgadas)", 0.1, 2.0, 0.5)

def generar_pdf(input_pdf, start_num, font_size, margin_top):
    reader = PdfReader(input_pdf)
    writer = PdfWriter()
    
    # Medidas Oficio 8.3 x 13
    width = 8.3 * inch
    height = 13.0 * inch
    
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=(width, height))
    
    for i in range(len(reader.pages)):
        current_num = start_num + i
        word = num2words(current_num, lang='es').capitalize()
        text = f"{current_num}. {word}"
        
        can.setFont("Courier-Bold", font_size)
        can.drawCentredString(width / 2, height - (margin_top * inch), text)
        can.showPage()
        
    can.save()
    packet.seek(0)
    overlay = PdfReader(packet)

    for i in range(len(reader.pages)):
        page = reader.pages[i]
        page.merge_page(overlay.pages[i])
        writer.add_page(page)
    
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()

if archivo_subido is not None:
    if st.button("🔢 Numerar PDF"):
        with st.spinner("Procesando..."):
            resultado = generar_pdf(archivo_subido, numero_inicial, tamaño_fuente, margen_superior)
            st.success("¡PDF procesado con éxito!")
            st.download_button(
                label="📥 Descargar PDF Numerado",
                data=resultado,
                file_name="pdf_numerado.pdf",
                mime="application/pdf"
            )