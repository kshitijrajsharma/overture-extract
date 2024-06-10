import io
import os
import subprocess

import geopandas as gpd
import streamlit as st

st.title("Overture Maps Data Downloader")

data_types = [
    "locality",
    "locality_area",
    "administrative_boundary",
    "building",
    "building_part",
    "division",
    "division_area",
    "place",
    "segment",
    "connector",
    "infrastructure",
    "land",
    "land_use",
    "water",
]

type_theme_map = {
    "locality": "admins",
    "locality_area": "admins",
    "administrative_boundary": "admins",
    "building": "buildings",
    "building_part": "buildings",
    "division": "divisions",
    "division_area": "divisions",
    "place": "places",
    "segment": "transportation",
    "connector": "transportation",
    "infrastructure": "base",
    "land": "base",
    "land_use": "base",
    "water": "base",
}

file_formats = ["geojson", "geojsonseq", "geoparquet"]

input_option = st.sidebar.radio("Input Option", ["Paste GeoJSON", "Upload File"])
data_type = st.sidebar.selectbox("Data Type", data_types)
file_format = st.sidebar.selectbox("File Format", file_formats)
version = st.sidebar.text_input("Version", value="2024-05-16-beta.0")
custom_theme = st.sidebar.text_input("Theme", value=type_theme_map.get(data_type, ""))
custom_type = st.sidebar.text_input("Type", value=data_type)

if input_option == "Paste GeoJSON":
    geojson_input = st.text_area("Paste GeoJSON")
    if geojson_input:
        gdf = gpd.GeoDataFrame.from_features(eval(geojson_input))
        bbox = gdf.total_bounds
        st.write(f"Calculated Bounding Box: {bbox}")
elif input_option == "Upload File":
    uploaded_file = st.file_uploader("Choose a File")
    if uploaded_file is not None:
        if uploaded_file.name.endswith(".geojson"):
            gdf = gpd.read_file(io.BytesIO(uploaded_file.getvalue()))
        elif uploaded_file.name.endswith(".parquet"):
            gdf = gpd.read_parquet(io.BytesIO(uploaded_file.getvalue()))
        else:
            st.error("Invalid file format. Please upload a GeoJSON or GeoParquet file.")
        bbox = gdf.total_bounds
        st.write(f"Calculated Bounding Box: {bbox}")

if st.button("Download Data"):
    with st.spinner("Downloading data..."):
        url = f"overturemaps-us-west-2/release/{version}/theme={custom_theme}/type={custom_type}/"
        st.write(f"Downloading data from: {url}")

        bbox_str = ",".join(map(str, bbox))
        cmd = [
            "overturemaps",
            "download",
            "-f",
            file_format,
            "--bbox",
            bbox_str,
            "-o",
            f"output_{custom_theme}_{custom_type}.{file_format}",
            "-r",
            version,
            "-cth",
            custom_theme,
            "-cty",
            custom_type,
        ]

        try:
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            while True:
                output = process.stdout.readline()
                if output == "" and process.poll() is not None:
                    break
                if output:
                    st.code(output.strip(), language="bash")
            rc = process.poll()
            if rc == 0:
                st.success("Data downloaded successfully!")
                output_file = f"output_{custom_theme}_{custom_type}.{file_format}"
                file_size = os.path.getsize(output_file)
                file_size_mb = file_size / (1024 * 1024)
                file_size_str = f"{file_size_mb:.2f} MB"
                file_info = f"{output_file} ({file_size_str})"

                st.download_button(
                    label=file_info,
                    data=open(output_file, "rb").read(),
                    file_name=output_file,
                    mime=f"application/{file_format}",
                )
            else:
                stderr = process.stderr.read()
                st.error(f"Error downloading data: {stderr}")
        except subprocess.CalledProcessError as e:
            st.error(f"Error downloading data: {e.stderr}")
