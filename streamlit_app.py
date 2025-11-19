import streamlit as st
import requests
import json
import base64

st.set_page_config(page_title="Printer Control", page_icon="🖨️")

st.title("🖨️ Receipt Printer Control")

# Sidebar for Server Status
with st.sidebar:
    st.header("Server Status")
    if st.button("Check Connection"):
        try:
            response = requests.get("http://localhost:5000/health")
            if response.status_code == 200:
                st.success("Connected to Print Server")
                st.json(response.json())
            else:
                st.error(f"Server Error: {response.status_code}")
        except requests.exceptions.ConnectionError:
            st.error("Could not connect to server. Is it running?")

# Main Form
with st.form("print_form"):
    st.subheader("Compose Receipt")
    
    header_text = st.text_input("Header (Optional)", placeholder="e.g. My Store")
    
    body_text = st.text_area("Receipt Text", height=150, placeholder="Item 1... $10.00\nItem 2... $5.00")
    
    uploaded_file = st.file_uploader("Choose an image", type=['png', 'jpg', 'jpeg'])
    
    col1, col2 = st.columns(2)
    
    with col1:
        align = st.selectbox("Alignment", ["left", "center", "right"])
        font_style = st.selectbox("Font Style", ["default", "montserrat", "kings"])
        font_size = st.slider("Font Size", min_value=12, max_value=72, value=24, step=2)
        is_bold = st.checkbox("Bold Text")
        
    with col2:
        cut_paper = st.checkbox("Cut Paper", value=True)
    
    submitted = st.form_submit_button("🖨️ Print Receipt")
    
    if submitted:
        if not body_text and not header_text and not uploaded_file:
            st.warning("Please enter some text or upload an image to print.")
        else:
            # Add padding to prevent cutoff
            final_text = body_text + "\n" * 4 if body_text else "\n" * 4
            
            payload = {
                "text": final_text,
                "header": header_text,
                "bold": is_bold,
                "align": align,
                "cut": cut_paper,
                "font_style": font_style,
                "font_size": font_size
            }
            
            if uploaded_file is not None:
                # Convert to base64
                bytes_data = uploaded_file.getvalue()
                base64_image = base64.b64encode(bytes_data).decode('utf-8')
                payload['image'] = base64_image
            
            try:
                with st.spinner("Sending to printer..."):
                    response = requests.post("http://localhost:5000/print", json=payload)
                
                if response.status_code == 200:
                    st.success("Print job sent successfully!")
                    st.json(response.json())
                else:
                    st.error(f"Failed to print: {response.text}")
            except requests.exceptions.ConnectionError:
                st.error("Could not connect to print server. Please ensure it is running on port 5000.")
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

st.markdown("---")
st.markdown("*Printer Control Panel v1.0*")
