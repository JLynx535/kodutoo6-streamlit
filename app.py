import json
from io import StringIO

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

STATISTIKAAMETI_API_URL="https://andmed.stat.ee/api/v1/et/stat/RV032"
GEOJSON_FILE="maakonnad.geojson"

JSON_PAYLOAD={
    "query":[
        {
            "code":"Aasta",
            "selection":{
                "filter":"item",
                "values":["2014", "2015", "2016", "2017", "2018", "2019", "2020", "2021", "2022", "2023"]
            }
        },
        {
            "code":"Maakond",
            "selection":{
                "filter":"item",
                "values":["39", "44", "49", "51", "57", "59", "65", "67", "70", "74", "78", "82", "84", "86", "37"]
            }
        },
        {
            "code":"Sugu",
            "selection":{
                "filter":"item",
                "values":["2", "3"]
            }
        }
    ],
    "response":{
        "format":"csv"
    }
}


@st.cache_data
def import_data():
    headers={"Content-Type":"application/json"}
    response=requests.post(STATISTIKAAMETI_API_URL, json=JSON_PAYLOAD, headers=headers, timeout=30)
    response.raise_for_status()

    text=response.content.decode("utf-8-sig")
    df=pd.read_csv(StringIO(text))
    df["Aasta"]=df["Aasta"].astype(int)
    df["Loomulik iive"]=df["Mehed Loomulik iive"]+df["Naised Loomulik iive"]
    return df


@st.cache_data
def import_geojson():
    with open(GEOJSON_FILE, encoding="utf-8") as file:
        return json.load(file)


def get_data_for_year(df, year):
    return df[df["Aasta"]==year].copy()


def make_map(year_data, counties, year, selected_metric):
    fig=px.choropleth(
        year_data,
        geojson=counties,
        locations="Maakond",
        featureidkey="properties.MNIMI",
        color=selected_metric,
        hover_name="Maakond",
        hover_data={
            "Aasta":True,
            "Mehed Loomulik iive":True,
            "Naised Loomulik iive":True,
            "Loomulik iive":True
        },
        color_continuous_scale="Viridis",
        title=f"{selected_metric} maakonniti aastal {year}"
    )
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin={"r":0, "t":50, "l":0, "b":0})
    return fig


st.set_page_config(page_title="Loomulik iive maakonniti", layout="wide")

st.title("Loomulik iive Eesti maakondades")
st.write("Töölaud kasutab Statistikaameti andmeid ning kuvab loomuliku iibe maakondade kaupa."
    "See dashboard kuvab Eesti maakondade loomulikku iivet aastatel 2014–2023. "
    "Kasutaja saab valida aasta ning vaadata, millistes maakondades oli loomulik iive suurem või väiksem. " 
    " Kaardi peale kursoriga minnes annab vastava maakonna valitud aasta ülevaate."
    "Lisaks saab eraldi vaadata kogu loomulikku iivet ning meeste ja naiste arvestust. "
    "Andmeid saab vaadata ka tabelina ning vajadusel CSV-failina alla laadida."
)

df=import_data()
counties=import_geojson()

years=sorted(df["Aasta"].unique())
selected_year=st.sidebar.selectbox("Vali aasta", years, index=len(years)-1)

metric_options={
    "Kokku":"Loomulik iive",
    "Mehed":"Mehed Loomulik iive",
    "Naised":"Naised Loomulik iive"
}

selected_metric_label=st.sidebar.selectbox("Vali näitaja", list(metric_options.keys()))
selected_metric=metric_options[selected_metric_label]

year_data=get_data_for_year(df, selected_year)

fig=make_map(year_data, counties, selected_year, selected_metric)
st.plotly_chart(fig, use_container_width=True)

st.subheader("Andmetabel")
table_data=year_data[["Aasta", "Maakond", "Mehed Loomulik iive", "Naised Loomulik iive", "Loomulik iive"]].sort_values(selected_metric, ascending=True)

st.dataframe(table_data, use_container_width=True)

csv=table_data.to_csv(index=False).encode("utf-8-sig")
st.sidebar.download_button(
    label="Lae tabel CSV-failina alla",
    data=csv,
    file_name=f"loomulik_iive_{selected_year}_{selected_metric_label.lower()}.csv",
    mime="text/csv"
)

st.caption("Allikas: Statistikaamet, tabel RV032.")