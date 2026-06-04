import streamlit as st
import fitz  # PyMuPDF
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import io

st.set_page_config(page_title="PDF Editor Mobile", layout="centered")
st.title("PDF Editor - Android")

# Simpan foto scan sementara
if "scan_images" not in st.session_state:
    st.session_state.scan_images = []

tab1, tab2 = st.tabs(["Edit PDF", "Camera to PDF"])

# ========== TAB 1: EDIT PDF - TAMPILAN MIRIP FOXIT ==========
with tab1:
    st.markdown("""
        <style>
        .foxit-toolbar {
            background-color: #f0f0f0;
            padding: 8px;
            border-radius: 5px;
            margin-bottom: 10px;
            border: 1px solid #ddd;
        }
        </style>
    """, unsafe_allow_html=True)
    
    uploaded = st.file_uploader("Upload PDF", type="pdf", key="upload_edit")
    
    if uploaded:
        doc = fitz.open(stream=uploaded.read(), filetype="pdf")
        total_pages = len(doc)
        
        # Toolbar navigasi mirip Foxit
        col1, col2, col3, col4 = st.columns([1, 1, 2, 1])
        
        with col1:
            if st.button("⏮️", use_container_width=True, help="Halaman Pertama"):
                st.session_state.page_edit = 1
                st.rerun()
        with col2:
            if st.button("⏪", use_container_width=True, help="Sebelumnya"):
                current = st.session_state.get("page_edit", 1)
                if current > 1:
                    st.session_state.page_edit = current - 1
                    st.rerun()
        with col3:
            page_num = st.number_input(
                "Halaman", 1, total_pages, 
                value=st.session_state.get("page_edit", 1), 
                key="page_edit", 
                label_visibility="collapsed"
            ) - 1
        with col4:
            if st.button("⏩", use_container_width=True, help="Selanjutnya"):
                current = st.session_state.get("page_edit", 1)
                if current < total_pages:
                    st.session_state.page_edit = current + 1
                    st.rerun()
        
        page = doc[page_num]
        
        # Zoom control
        zoom = st.slider("Zoom", 0.5, 3.0, 1.5, 0.1, label_visibility="collapsed")
        scale_factor = zoom
        
        # Render halaman PDF jadi gambar
        pix = page.get_pixmap(matrix=fitz.Matrix(scale_factor, scale_factor))
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        st.caption(f"Halaman {page_num+1} dari {total_pages}")
        st.image(img, use_column_width=True)
        
        st.markdown("---")
        st.write("**Mode Edit:** Drag kotak merah buat nutup teks yang mau dihapus")
        
        # Canvas buat gambar kotak merah
        canvas_result = st_canvas(
            fill_color="rgba(255, 0, 0, 0.3)",
            stroke_width=4,
            stroke_color="red",
            background_color="rgba(0,0,0,0)",
            height=400,
            drawing_mode="rect",
            key="canvas_edit",
        )
        
        # Panel tambah teks
        with st.expander("➕ Tambah Teks Baru", expanded=False):
            new_text = st.text_input("Ketik teks:")
            col1, col2, col3 = st.columns(3)
            with col1:
                fontsize = st.number_input("Font:", 8, 72, 12)
            with col2:
                text_pos_x = st.number_input("X:", 0, img.width, 50, key="x")
            with col3:
                text_pos_y = st.number_input("Y:", 0, img.height, 50, key="y")
        else:
            new_text, fontsize, text_pos_x, text_pos_y = "", 12, 50, 50
        
        if st.button("💾 Simpan Edit", type="primary", use_container_width=True):
            if canvas_result.json_data and canvas_result.json_data.get("objects"):
                for obj in canvas_result.json_data["objects"]:
                    if obj["type"] == "rect":
                        x0 = obj["left"] / scale_factor
                        y0 = obj["top"] / scale_factor
                        x1 = (obj["left"] + obj["width"]) / scale_factor
                        y1 = (obj["top"] + obj["height"]) / scale_factor
                        page.add_redact_annot(fitz.Rect(x0, y0, x1, y1), fill=(1, 1, 1))
                page.apply_redactions()
            
            if new_text:
                page.insert_text((text_pos_x / scale_factor, text_pos_y / scale_factor), 
                                 new_text, fontsize=fontsize, color=(0, 0, 0))
            
            buf = io.BytesIO()
            doc.save(buf)
            buf.seek(0)
            st.download_button("📥 Download PDF Hasil Edit", buf, "edited.pdf", 
                               "application/pdf", use_container_width=True)

# ========== TAB 2: CAMERA TO PDF MULTI HALAMAN ==========
with tab2:
    st.write("Foto dokumen halaman per halaman")
    
    camera_image = st.camera_input("Ambil Foto Halaman")
    
    if camera_image:
        img = Image.open(camera_image).convert("RGB")
        st.session_state.scan_images.append(img)
        st.success(f"Halaman {len(st.session_state.scan_images)} ditambahkan")
    
    if st.session_state.scan_images:
        st.write(f"Total halaman: {len(st.session_state.scan_images)}")
        
        # Preview semua halaman
        for i, img in enumerate(st.session_state.scan_images):
            st.image(img, caption=f"Halaman {i+1}", width=200)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Tambah Halaman Lagi", use_container_width=True):
                st.rerun()
        with col2:
            if st.button("Buat PDF", type="primary", use_container_width=True):
                pdf_doc = fitz.open()
                for img in st.session_state.scan_images:
                    img_bytes = io.BytesIO()
                    img.save(img_bytes, format="PNG")
                    img_bytes.seek(0)
                    
                    rect = fitz.Rect(0, 0, img.width, img.height)
                    page = pdf_doc.new_page(width=img.width, height=img.height)
                    page.insert_image(rect, stream=img_bytes.getvalue())
                
                buf = io.BytesIO()
                pdf_doc.save(buf)
                buf.seek(0)
                st.download_button(
                    "📥 Download PDF Hasil Scan", 
                    buf, 
                    "scan_multi.pdf", 
                    "application/pdf",
                    use_container_width=True
                )
        
        if st.button("Reset / Hapus Semua", use_container_width=True):
            st.session_state.scan_images = []
            st.rerun()