import streamlit as st
import fitz
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import io
import base64

st.set_page_config(page_title="PDF Editor", layout="wide")
st.title("📄 PDF Editor - Hapus & Tambah Teks")

uploaded_file = st.file_uploader("Upload PDF", type="pdf")

if uploaded_file is not None:
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    
    page_num = st.number_input("Pilih Halaman", 1, len(doc), 1) - 1
    page = doc[page_num]
    
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    
    # Convert PIL Image ke bytes buat st_canvas
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_bytes = buffered.getvalue()
    
    st.write("**Gambar PDF - Arsir area yang mau dihapus**")
    canvas_result = st_canvas(
        fill_color="rgba(255, 0, 0, 0.3)",
        stroke_width=20,
        stroke_color="rgba(255, 0, 0, 0.3)",
        background_image=img_bytes,  # pakai bytes bukan PIL Image
        update_streamlit=True,
        height=pix.height,
        width=pix.width,
        drawing_mode="rect",
        key="canvas"
    )
    
    new_text = st.text_input("Teks baru yang mau ditambah:")
    text_x = st.number_input("Posisi X teks", 0, pix.width, 50)
    text_y = st.number_input("Posisi Y teks", 0, pix.height, 50)
    font_size = st.slider("Ukuran font", 8, 40, 16)
    
    if st.button("Proses PDF"):
        if canvas_result.json_data is not None:
            for obj in canvas_result.json_data["objects"]:
                if obj["type"] == "rect":
                    rect = fitz.Rect(obj["left"]/2, obj["top"]/2, 
                                   (obj["left"]+obj["width"])/2, 
                                   (obj["top"]+obj["height"])/2)
                    page.add_redact_annot(rect, fill=(1, 1, 1))
            page.apply_redactions()
        
        if new_text:
            page.insert_text((text_x/2, text_y/2), new_text, fontsize=font_size/2)
        
        output = io.BytesIO()
        doc.save(output)
        output.seek(0)
        
        st.download_button("Download PDF Hasil", output, "hasil_edit.pdf")
else:
    st.info("Upload file PDF dulu ya")