import streamlit as st
from extract_searches import GoogleScholarProvider
import pandas as pd
from string import Template
import os

current_dir = os.path.abspath(os.getcwd())
driver_bin = os.path.join(current_dir, "driver")
os.environ["PATH"] += os.pathsep + driver_bin


def main():
    st.title("Google Scholar Downloader")

    query = st.text_input("Enter Query")
    query = query.replace(" ", "+")
    url = "https://scholar.google.com/scholar?start=$index&q=$query&hl=en&as_sdt=0,5&as_ylo=$since_year&as_vis=1"
    container = st.container()
    start = container.number_input("Start", min_value=0, max_value=100, value=0)
    max = container.number_input(
        "Max", min_value=start, max_value=200, value=10, step=10
    )
    step = container.number_input("Step", min_value=1, value=10)
    since_year = st.number_input(
        "Since Year", min_value=1900, max_value=2025, value=2020
    )

    download = st.checkbox("Download PDFs if available")
    if st.button("Download"):
        papers = []
        for i in range(start, max, step):
            url_ = Template(url).substitute(index=i, query=query, since_year=since_year)
            st.write(f"Downloading... {url_}")
            provider = GoogleScholarProvider(url_, cache=True)
            papers.extend(provider.get_all_papers(st, download))

        if papers:
            df = pd.DataFrame(papers)
            st.write(df)
        else:
            st.write("No papers found.")


if __name__ == "__main__":
    main()
