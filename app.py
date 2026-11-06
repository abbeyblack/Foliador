import streamlit as st
import io
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from num2words import num2words

# Configuración básica de la página
st.set_page_config(page_title="Foliador UIE", layout="centered")

st.title("📄 Foliador")
st.write("Configura el inicio de la numeración y sube tu archivo.")

# --- VALORES PREDETERMINADOS (FIJOS) ---
FONT_SIZE = 12
MARGEN_SUPERIOR = 0.5


def crear_overlay(width, height, rotation, texto):
    """
    Crea una página PDF (en memoria) con el texto centrado en la parte
    superior, tal como se ve la hoja una vez aplicada la rotación.
    Devuelve la página del overlay.
    """
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=(width, height))
    can.setFont("Courier-Bold", FONT_SIZE)

    margen = MARGEN_SUPERIOR * inch

    if rotation == 0:
        can.drawCentredString(width / 2, height - margen, texto)
    elif rotation == 90:
        can.saveState()
        can.translate(margen, height / 2)
        can.rotate(-90)
        can.drawCentredString(0, 0, texto)
        can.restoreState()
    elif rotation == 180:
        can.saveState()
        can.translate(width / 2, margen)
        can.rotate(180)
        can.drawCentredString(0, 0, texto)
        can.restoreState()
    elif rotation == 270:
        can.saveState()
        can.translate(width - margen, height / 2)
        can.rotate(90)
        can.drawCentredString(0, 0, texto)
        can.restoreState()
    else:
        can.drawCentredString(width / 2, height - margen, texto)

    can.save()
    packet.seek(0)
    return PdfReader(packet).pages[0]


# --- PANEL LATERAL (CONFIGURACIÓN + FAQ) ---
with st.sidebar:
    st.header("⚙️ Configuración")
    numero_a_escribir = st.number_input("¿Con qué número empezar?", value=1, min_value=0)
    pagina_donde_empieza = st.number_input("¿En qué página del PDF empezar?", value=1, min_value=1)
    # 0 significa "hasta el final del documento"
    pagina_donde_termina = st.number_input("¿En qué página del PDF terminar? (0 = todas)", value=0, min_value=0)

    st.divider()  # Línea divisoria

    # --- SECCIÓN DE FAQ ---
    st.subheader("❓ Preguntas Frecuentes")

    with st.expander("¿Qué hace esta app?"):
        st.write("""
            Esta herramienta agrega números de página en formato **'1. Uno'** centrados en la parte superior. Está optimizada para hojas tamaño 
            **Oficio (8.3\" x 13\")**. Conserva los marcadores (bookmarks) del archivo original.
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

    with st.expander("¿Qué significa '0' en página de término?"):
        st.write("""
            Cuando el valor es **0**, la app enumera **todas las páginas** 
            desde la página de inicio hasta el final del documento, 
            sin importar cuántas tenga.
        """)

# --- LÓGICA DE PROCESAMIENTO ---
archivo_subido = st.file_uploader("Sube tu archivo PDF", type="pdf")

if archivo_subido:
    if st.button("🚀 Generar PDF Numerado"):
        try:
            with st.spinner("Procesando..."):
                reader = PdfReader(archivo_subido)

                # Si el PDF está cifrado sin contraseña de apertura, se intenta abrir
                if reader.is_encrypted:
                    reader.decrypt("")

                # Clona TODO el documento (páginas, bookmarks, metadatos, etc.)
                writer = PdfWriter(clone_from=reader)

                # Si pagina_donde_termina es 0, se usa el total de páginas del PDF
                total_paginas = len(writer.pages)
                limite_final = total_paginas if pagina_donde_termina == 0 else pagina_donde_termina

                for i, page in enumerate(writer.pages):
                    numero_pagina_actual = i + 1

                    if pagina_donde_empieza <= numero_pagina_actual <= limite_final:
                        conteo_actual = numero_a_escribir + (numero_pagina_actual - pagina_donde_empieza)
                        word = num2words(conteo_actual, lang='es').capitalize()
                        texto = f"{conteo_actual}. {word}"

                        width = float(page.mediabox.width)
                        height = float(page.mediabox.height)
                        rotation = int(page.get("/Rotate", 0) or 0) % 360

                        overlay_page = crear_overlay(width, height, rotation, texto)

                        # La página ya pertenece al writer, así que se puede fusionar
                        page.merge_page(overlay_page)

                output = io.BytesIO()
                writer.write(output)
                output.seek(0)

                st.success("✅ ¡PDF listo!")
                st.download_button(
                    label="📥 Descargar ahora",
                    data=output,
                    file_name="archivo_numerado.pdf",
                    mime="application/pdf"
                )
        except Exception as e:
            st.error(f"Error al procesar: {e}")
