import streamlit as st
import os
import json
import pandas as pd


def fetch_all_jsons(directory):
    json_files = []
    for filename in os.listdir(directory):
        if filename.endswith(".json"):
            with open(os.path.join(directory, filename), "r") as file:
                json_files.append(json.load(file))
    return json_files


st.title("Downloaded papers")
if st.button("Run"):
    json_data = fetch_all_jsons(".data/results/")
    json_data.sort(key=lambda x: x["title"])
    # df = pd.DataFrame(json_data)
    # df = df[["title", "author", "abstract", "url"]]
    # # st.write(json_data)
    # st.dataframe(df)
    for data in json_data:
        c = st.container()
        c.subheader(data["title"])
        c.write(data["author"])
        c.link_button("Visit", data["url"])
        if data["abstract"] != "Abstract not found":
            c.write(f"{data['abstract']}")
