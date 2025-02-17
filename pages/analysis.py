import streamlit as st
import os
import json
import subprocess
from providers.provider import DOWNLOAD_DIR, NOTES_DIR, Provider


def fetch_all_jsons(directory):
    json_files = []
    for filename in os.listdir(directory):
        if filename.endswith(".json"):
            with open(os.path.join(directory, filename), "r") as file:
                json_files.append(json.load(file))
    return json_files


def fetch_all_pdfs(directory):
    pdf_files = {}
    # filenames = []
    for filename in os.listdir(directory):
        if filename.endswith(".pdf"):
            pdf_files[os.path.splitext(filename)[0]] = os.path.join(directory, filename)
    return pdf_files


PDFs = fetch_all_pdfs(DOWNLOAD_DIR)

# print(PDFs)


def check_pdf(data):
    if not data["download_url"]:
        return False
    f = Provider.generate_filename(data["title"])
    if f in PDFs:
        return PDFs[f]
    return False


def run(cmd):
    completed = subprocess.run(["powershell", "-Command", cmd], capture_output=True)
    return completed


def open_notepad(filepath):
    run(f'code "{filepath}"')


def open_file(pdfLink):
    run(f'Start "{pdfLink}"')


st.title("Downloaded papers")

json_data = fetch_all_jsons(".data/results/")
# json_data = list(set(json_data))
json_data.sort(key=lambda x: x["title"])


# df = pd.DataFrame(json_data)
# df = df[["title", "author", "abstract", "url"]]
# # st.write(json_data)
# st.dataframe(df)
def render_pdf_actions(check_pdf, open_pdf, i, data):
    expander_c = st.expander(data["title"])
    expander_c.write(data["author"])
    # c.link_button("Visit", data["url"])
    if data["abstract"] != "Abstract not found":
        expander_c.write(f"{data['abstract']}")
    pdfLink = check_pdf(data)
    print(pdfLink)
    container = expander_c.container(border=True)
    container.link_button("Visit", data["url"])
    if container.button("Open Notes", key=f"notes_{i}"):
        note = Provider.generate_filename(data["title"]) + ".md"
        filepath = os.path.join(NOTES_DIR, note)
        if not os.path.exists(filepath):
            with open(filepath, "w") as f:
                f.write(f"# {data['title']}\n\n")
                f.write(f"## Authors\n\n{data['author']}\n\n")
                f.write(f"## Abstract\n\n{data['abstract']}\n\n")
                f.write(f"## URL\n\n{data['url']}\n\n")
                f.write(f"# Notes")
        open_notepad(filepath)
    if pdfLink is not False:
        if container.button("Open PDF", key=i):
            open_pdf(pdfLink)
    else:
        container.write(f"PDF not available : {pdfLink}")


for i, data in enumerate(json_data):
    render_pdf_actions(check_pdf, open_file, i, data)
