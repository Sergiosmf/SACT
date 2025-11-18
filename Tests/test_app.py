import streamlit as st

st.title("🚛 Sistema CT-e - Teste")

menu = st.selectbox("Selecione:", ["Processamento", "Visualização"])

if menu == "Visualização":
    st.success("✅ Visualizações estão funcionando!")
    st.write("Esta é a área de visualizações")
else:
    st.info("Esta é a área de processamento")