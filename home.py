import streamlit as st
from extract_searches import GoogleScholarProvider
import pandas as pd
from string import Template


def main():
    st.title("Google Scholar Downloader")

    query = st.text_input("Enter URL:")
    query = query.replace(" ", "+")
    url = "https://scholar.google.com/scholar?start=$index&q=$query&hl=en&as_sdt=0,5"
    container = st.container()
    start = container.number_input("Start", min_value=0, max_value=100, value=0)
    max = container.number_input("Max", min_value=start, max_value=100, value=10)
    step = container.number_input("Step", min_value=1, value=10)

    if st.button("Download"):
        papers = []
        for i in range(start, max, step):
            url_ = Template(url).substitute(index=i, query=query)
            st.write(f"Downloading... {url_}")
            provider = GoogleScholarProvider(url_, cache=True)
            papers.extend(provider.get_all_papers(st))

        if papers:
            df = pd.DataFrame(papers)
            st.write(df)
        else:
            st.write("No papers found.")


if __name__ == "__main__":
    main()
