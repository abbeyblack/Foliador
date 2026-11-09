import streamlit as st
import io
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from num2words import num2words

# Configuración básica de la página
st.set_page_config(page_title="Foliador UIE", layout="centered")

st.title("📄 Foliador")
st.write("Configura el inicio de la numeración y sube tu archivo. Si tienes dudas sobre cómo usar la App, revisa las Preguntas Frecuentes (FAQ) en el menú lateral.")

# --- VALORES PREDETERMINADOS (FIJOS) ---
FONT_SIZE = 12
MARGEN_SUPERIOR = 0.5


def crear_overlay(left, bottom, width, height, rotation, texto):
    """
    Crea una página PDF (en memoria) con el texto centrado en el borde
    superior VISUAL de la hoja, derecho y legible, sin importar si la
    hoja tiene /Rotate de 0, 90, 180 o 270 grados.
    """
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=(left + width, bottom + height))
    can.setFont("Courier-Bold", FONT_SIZE)

    margen = MARGEN_SUPERIOR * inch

    can.saveState()
    # Se ajusta al origen real del mediabox (normalmente 0, 0)
    can.translate(left, bottom)

    if rotation == 90:
        # El borde superior visual es el borde izquierdo de la hoja sin rotar
        can.translate(margen, height / 2)
        can.rotate(90)
    elif rotation == 180:
        # El borde superior visual es el borde inferior de la hoja sin rotar
        can.translate(width / 2, margen)
        can.rotate(180)
    elif rotation == 270:
        # El borde superior visual es el borde derecho de la hoja sin rotar
        can.translate(width - margen, height / 2)
        can.rotate(-90)
    else:
        # Rotación 0: arriba, centrado
        can.translate(width / 2, height - margen)

    can.drawCentredString(0, 0, texto)
    can.restoreState()

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
archivo_subido = st.file_uploader("Sube tu expediente", type="pdf")

if archivo_subido:
    if st.button("🚀 Generar expediente foliado"):
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

                        left = float(page.mediabox.left)
                        bottom = float(page.mediabox.bottom)
                        width = float(page.mediabox.width)
                        height = float(page.mediabox.height)
                        rotation = int(page.get("/Rotate", 0) or 0) % 360

                        overlay_page = crear_overlay(left, bottom, width, height, rotation, texto)

                        # La página ya pertenece al writer, así que se puede fusionar
                        page.merge_page(overlay_page)

                output = io.BytesIO()
                writer.write(output)
                output.seek(0)

                st.success("✅ ¡Expediente listo!")
                st.download_button(
                    label="📥 Descargar ahora",
                    data=output,
                    file_name="expediente_numerado.pdf",
                    mime="application/pdf"
                )
        except Exception as e:
            st.error(f"Error al procesar: {e}")
