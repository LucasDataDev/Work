import io
import pdfplumber
import pandas as pd
import streamlit as st

# ====== Funções reutilizadas do seu script ======
def filtrar_servicos(texto: str):
    linhas = texto.split('\n')
    servicos = []
    dentro_servicos = False

    for linha in linhas:
        linha_limpa = linha.strip().lower()

        if "serviço" in linha_limpa or "serviços" in linha_limpa:
            dentro_servicos = True
            continue

        if "mão de obra" in linha_limpa:
            dentro_servicos = False
            break

        if dentro_servicos and linha.strip():
            servicos.append(linha.strip())
    return servicos

def limpar_texto(texto: str):
    return (texto.replace('ç', 'c').replace('ã', 'a').replace('á', 'a')
                 .replace('é', 'e').replace('í', 'i').replace('ó', 'o')
                 .replace('ú', 'u').replace('â', 'a').replace('ê', 'e')
                 .replace('ô', 'o').replace('Ç', 'C').replace('Ã', 'A')
                 .replace('Á', 'A').replace('É', 'E').replace('Í', 'I')
                 .replace('Ó', 'O').replace('Ú', 'U').replace('Â', 'A')
                 .replace('Ê', 'E').replace('Ô', 'O').strip())

def comparar_itens(itens_pdf1, itens_pdf2):
    itens_mantidos, itens_alterados, itens_removidos, itens_incluidos = [], [], [], []

    itens_pdf1_limpo = [limpar_texto(item) for item in itens_pdf1]
    itens_pdf2_limpo = [limpar_texto(item) for item in itens_pdf2]

    dict_pdf1 = {item: item for item in itens_pdf1_limpo}
    dict_pdf2 = {item: item for item in itens_pdf2_limpo}

    for item in dict_pdf1:
        if item in dict_pdf2:
            itens_mantidos.append(item)
        else:
            itens_removidos.append(item)

    for item in dict_pdf2:
        if item not in dict_pdf1:
            itens_incluidos.append(item)

    return itens_mantidos, itens_alterados, itens_removidos, itens_incluidos

def gerar_tabela_comparacao(servicos_resultados):
    tabela = pd.DataFrame(columns=["Categoria", "Item do Orçamento 1", "Status", "Item do Orçamento 2"])
    mantidos, alterados, removidos, incluidos = servicos_resultados

    for item in mantidos:
        tabela.loc[len(tabela)] = ["Serviços", item, "Manteve", item]
    for item in removidos:
        tabela.loc[len(tabela)] = ["Serviços", item, "Removido", ""]
    for item in incluidos:
        tabela.loc[len(tabela)] = ["Serviços", "", "Incluído", item]

    return tabela

def extrair_texto_pdf(file_like):
    # pdfplumber aceita arquivo em bytes (UploadedFile do Streamlit)
    with pdfplumber.open(file_like) as pdf:
        return ''.join([page.extract_text() or "" for page in pdf.pages])

# ====== UI Streamlit ======
st.set_page_config(page_title="Comparar PDFs – Serviços", layout="centered")
st.title("Comparar PDFs de Orçamento (Serviços)")

st.markdown(
    "Faça upload de **dois PDFs** do orçamento. O app extrai a seção **Serviços** "
    "e gera uma **tabela de diferenças** (mantidos, incluídos e removidos)."
)

col1, col2 = st.columns(2)
with col1:
    pdf1 = st.file_uploader("PDF 1 (versão anterior)", type=["pdf"], key="pdf1")
with col2:
    pdf2 = st.file_uploader("PDF 2 (versão nova)", type=["pdf"], key="pdf2")

if pdf1 and pdf2:
    with st.spinner("Extraindo textos e comparando..."):
        texto1 = extrair_texto_pdf(pdf1)
        texto2 = extrair_texto_pdf(pdf2)

        servicos_pdf1 = filtrar_servicos(texto1)
        servicos_pdf2 = filtrar_servicos(texto2)

        resultados = comparar_itens(servicos_pdf1, servicos_pdf2)
        tabela = gerar_tabela_comparacao(resultados)

    # Resumo
    mantidos, alterados, removidos, incluidos = resultados
    st.subheader("Resumo")
    st.write(
        f"- Serviços no PDF 1: **{len(servicos_pdf1)}**  \n"
        f"- Serviços no PDF 2: **{len(servicos_pdf2)}**  \n"
        f"- Mantidos: **{len(mantidos)}**  \n"
        f"- Removidos: **{len(removidos)}**  \n"
        f"- Incluídos: **{len(incluidos)}**"
    )

    # Prévia da tabela
    st.subheader("Tabela de comparação")
    st.dataframe(tabela, use_container_width=True)

    # Downloads
    st.subheader("Exportar")
    # CSV
    csv_bytes = tabela.to_csv(index=False, sep=";", encoding="utf-8-sig").encode("utf-8-sig")
    st.download_button("⬇️ Baixar CSV", data=csv_bytes, file_name="tabela_comparacao_servicos.csv", mime="text/csv")

    # XLSX
    xlsx_buffer = io.BytesIO()
    with pd.ExcelWriter(xlsx_buffer, engine="openpyxl") as writer:
        tabela.to_excel(writer, sheet_name="Comparacao", index=False)
    st.download_button(
        "⬇️ Baixar XLSX",
        data=xlsx_buffer.getvalue(),
        file_name="tabela_comparacao_servicos.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

else:
    st.info("Carregue os dois arquivos PDF para iniciar a comparação.")
