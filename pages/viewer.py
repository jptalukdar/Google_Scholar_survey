import os
import json
import streamlit as st
import streamlit.components.v1 as components
from providers.provider import RESULTS_DIR


def read_json_files(directory):
    json_files = []
    for filename in os.listdir(directory):
        if filename.endswith(".json"):
            with open(os.path.join(directory, filename), "r") as file:
                f = json.load(file)
                f["filename"] = filename
                json_files.append(f)
    return json_files


def find_index(json_files, title):
    for i, j in enumerate(json_files):
        if j["title"] == title:
            return i
    return None


def main():
    st.title("JSON File Viewer")

    # directory = st.text_input("Enter the directory path:", "")
    # if not directory:
    #     st.warning("Please enter a directory path.")
    #     return

    json_files = read_json_files(RESULTS_DIR)
    if not json_files:
        st.warning("No JSON files found in the directory.")
        return

    selected_file = st.selectbox(
        "Select file:", [j["title"] for j in json_files], index=None
    )
    # st.number_input(
    #     "Select file index:", min_value=0, max_value=len(json_files) - 1, step=1
    # )

    if selected_file:
        index = find_index(json_files, selected_file)

        container = st.container()

        if container.button("Previous"):
            index = max(0, index - 1)

        if container.button("Next"):
            index = min(len(json_files) - 1, index + 1)

        res = json_files[index]
        # st.json()
        st.title(res["title"])
        st.write(res["author"])
        st.write(res["filename"])
        st.markdown(
            res["abstract"]
            if res["abstract"] != "Abstract not found"
            else res["snippet"]
        )

        notes = res.get("notes", "")
        written_notes = st.text_input("notes", res.get("notes", ""))
        if notes != written_notes:
            res["notes"] = written_notes
            with open(os.path.join(RESULTS_DIR, res["filename"]), "w") as f:
                json.dump(res, f, indent=4)

        # if st.button("View Page"):
        # components.iframe(res["url"], height=800)
        st.page_link(res["url"], label="View Page")


if __name__ == "__main__":
    main()
