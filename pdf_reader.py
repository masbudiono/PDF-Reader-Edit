import streamlit as st
import fitz  # PyMuPDF
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import io

st.set_page_config(page_title="PDF Reader + Edit", layout="wide")
st.title("PDF Reader + Edit")

uploaded = st.file_uploader("Upload PDF", type="pdf")

if uploaded:
    doc = fitz.open(stream=uploaded.read(), filetype="pdf")
    
    page_num = st.number_input("Pilih Halaman", 1, len(doc), 1, key="page") - 1
    page = doc[page_num]
    
    # Render PDF jadi gambar
    scale_factor = 1.5
    pix = page.get_pixmap(matrix=fitz.Matrix(scale_factor, scale_factor))
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    
    st.write("Drag kotak merah di gambar bawah buat nutup teks yang mau dihapus")
    
    # Tampilkan gambar PDF
    st.image(img, caption=f"Halaman {page_num+1}", use_column_width=True)
    
    # Canvas transparan buat gambar kotak merah
    canvas_result = st_canvas(
        fill_color="rgba(255, 0, 0, 0.3)",
        stroke_width=3,
        stroke_color="red",
        background_color="rgba(0,0,0,0)",
        update_streamlit=True,
        height=600,
        drawing_mode="rect",
        key="canvas",
    )
    
    st.write("---")
    col1, col2 = st.columns(2)
    with col1:
        new_text = st.text_input("Teks baru:")
        fontsize = st.number_input("Ukuran font:", 8, 72, 12)
    with col2:
        text_pos_x = st.number_input("Posisi X:", 0, img.width, 50)
        text_pos_y = st.number_input("Posisi Y:", 0, img.height, 50)
    
    if st.button("Simpan Edit", type="primary"):
        # 1. Hapus = gambar kotak putih
        if canvas_result.json_data and canvas_result.json_data.get("objects"):
            for obj in canvas_result.json_data["objects"]:
                if obj["type"] == "rect":
                    x0 = obj["left"] / scale_factor
                    y0 = obj["top"] / scale_factor
                    x1 = (obj["left"] + obj["width"]) / scale_factor
                    y1 = (obj["top"] + obj["height"]) / scale_factor
                    page.add_redact_annot(fitz.Rect(x0, y0, x1, y1), fill=(1, 1, 1))
            page.apply_redactions()
        
        # 2. Tambah teks
        if new_text:
            page.insert_text(
                (text_pos_x / scale_factor, text_pos_y / scale_factor), 
                new_text, 
                fontsize=fontsize, 
                color=(0, 0, 0)
            )
        
        buf = io.BytesIO()
        doc.save(buf)
        buf.seek(0)
        st.success("Berhasil!")
        st.download_button("Download PDF Hasil Edit", buf, "edited.pdf", "application/pdf")
else:
    st.info("Upload PDF dulu")