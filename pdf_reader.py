import streamlit as st
import fitz  # PyMuPDF
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import io

st.set_page_config(page_title="PDF Editor", layout="wide")
st.title("PDF Reader + Edit")

uploaded = st.file_uploader("Upload PDF", type="pdf")

if uploaded:
    doc = fitz.open(stream=uploaded.read(), filetype="pdf")
    
    page_num = st.number_input("Pilih Halaman", 1, len(doc), 1) - 1
    page = doc[page_num]
    
    # Render halaman jadi gambar
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2)) # 2x resolusi biar jernih
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    
    st.write("Klik-drag buat pilih area yang mau dihapus. Ketik teks baru di bawah kalau mau nambah.")
    
    # Canvas buat gambar kotak merah
    canvas_result = st_canvas(
        background_image=img,
        update_streamlit=True,
        height=600,
        drawing_mode="rect",
        stroke_color="red",
        stroke_width=3,
        key="canvas"
    )
    
    new_text = st.text_input("Teks baru yang mau ditambahkan:")
    text_pos_x = st.number_input("Posisi X teks baru:", 0, img.width, 50)
    text_pos_y = st.number_input("Posisi Y teks baru:", 0, img.height, 50)
    
    if st.button("Simpan Edit"):
        # 1. Hapus = gambar kotak putih di area yang di-select
        if canvas_result.json_data and canvas_result.json_data["objects"]:
            for obj in canvas_result.json_data["objects"]:
                if obj["type"] == "rect":
                    x0 = obj["left"] / 2  # bagi 2 karena pixmap 2x
                    y0 = obj["top"] / 2
                    x1 = (obj["left"] + obj["width"]) / 2
                    y1 = (obj["top"] + obj["height"]) / 2
                    page.add_redact_annot(fitz.Rect(x0, y0, x1, y1), fill=(1, 1, 1))
            page.apply_redactions()
        
        # 2. Tambah teks baru
        if new_text:
            page.insert_text((text_pos_x/2, text_pos_y/2), new_text, fontsize=12, color=(0, 0, 0))
        
        # Simpan PDF baru
        buf_img = io.BytesIO()
img.save(buf_img, format="PNG")
img_bytes = buf_img.getvalue()
background_image=img_bytes