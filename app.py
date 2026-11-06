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
            **Oficio (8.3" x 13")**. Conserva los marcadores (bookmarks) del archivo original.
        """)
    
    with st.expander("¿Cómo numero un expediente nuevo o sin folios previos?"):
        st.write("""
            Si tu documento no tiene ninguna página numerada y quieres foliarlo por completo, usa esta configuración:
            * **Número inicial a imprimir:** `1`
            * **Desde la página:** `1`
            * **Hasta la página:** `0` (esto aplicará la numeración hasta la última página).
        """)
    
    with st.expander("Mi expediente ya tiene folios y agregué hojas al final, ¿cómo continúo?"):
        st.write("""
            Para retomar la numeración justo donde la dejaste, sin alterar las páginas que ya están foliadas:
            * **Número inicial a imprimir:** El número siguiente al último folio que ya tienes (ej. si quedó en el 50, escribe `51`).
            * **Desde la página:** El número de página física del PDF donde comienzan estas hojas nuevas.
            * **Hasta la página:** `0` (para abarcar todas las hojas nuevas hasta el final).
        """)
    
    with st.expander("¿Qué hago si tengo hojas sin numerar en el medio del documento?"):
        st.write("""
            Si necesitas foliar solo un bloque específico en el centro de tu expediente, puedes aislar ese tramo indicando el rango exacto:
            * **Número inicial a imprimir:** El folio que le corresponde a la primera página de ese bloque.
            * **Desde la página:** El número de la página física del PDF donde inicia el bloque en blanco.
            * **Hasta la página:** La página exacta donde termina ese bloque. *(Importante: Aquí no debes usar 0, sino el número real donde finaliza el tramo).*
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
