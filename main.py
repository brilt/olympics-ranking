import streamlit as st
from curl_cffi import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

lang_code = "en"

# Define translations
translations = {
    "en": {
        "data_url":"https://olympics.com/en/paris-2024/medals",
        "page_title": "Olympics Ranking",
        "last_updated": "Last Updated",
        "reload_data": "Reload Data",
        "medals_explanation": r'''
            ### Explanation of Weighted Gold Score Calculation
            The **Weighted Gold Score** is calculated to provide a more balanced ranking by considering the relative value of each medal type. 
            The formula used is:
            $\text{Weighted Gold Score}=\text{Gold Medals} + \frac{\text{Silver Medals}}{2} + \frac{\text{Bronze Medals}}{3}$.
        ''',
        "error_parsing": "Error parsing element: ",
        "failed_retrieve": "Failed to retrieve the webpage. Status code: ",
        "sorted_by_medals": "Sorted by Number of Medals",
        "sorted_by_weighted_score": "Sorted by Weighted Gold Score",
        "rank_change": "Rank Change from Medals to Weighted Score",
    },
    "fr": {
        "data_url":"https://olympics.com/fr/paris-2024/medailles",
        "page_title": "Classement Olympique",
        "last_updated": "Dernière mise à jour",
        "reload_data": "Recharger les données",
        "medals_explanation": r'''
            ### Explication du calcul du score en or pondéré
            Le **score en or pondéré** est calculé pour fournir un classement plus équilibré en considérant la valeur relative de chaque type de médaille. 
            La formule utilisée est :
            $\text{Score en or pondéré}=\text{Médailles d'or} + \frac{\text{Médailles d'argent}}{2} + \frac{\text{Médailles de bronze}}{3}$.
        ''',
        "error_parsing": "Erreur lors de l'analyse de l'élément : ",
        "failed_retrieve": "Échec de la récupération de la page Web. Code de statut : ",
        "sorted_by_medals": "Trié par nombre de médailles",
        "sorted_by_weighted_score": "Trié par score en or pondéré",
        "rank_change": "Changement de classement des médailles au score pondéré",
    }
}

# Configure page
st.set_page_config(
    page_title=translations[lang_code]["page_title"],
    page_icon="🎖️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Select language
lang = st.sidebar.radio("Select Language / Sélectionnez la langue", ("English", "Français"))

# Map selected language to dictionary keys
lang_code = "en" if lang == "English" else "fr"


with st.sidebar:
    # Initialize session state for last updated time if not already present
    if 'last_updated' not in st.session_state:
        st.session_state['last_updated'] = None

    # Add a button to reload the data
    if st.button(translations[lang_code]["reload_data"]):
        st.rerun()
    # Display the last updated time
    st.info(f"{translations[lang_code]['last_updated']} {st.session_state['last_updated']}")

    # Explanation of the weighted calculation
    st.info(translations[lang_code]["medals_explanation"])

# Retrieve the webpage
response = requests.get(translations[lang_code]["data_url"], impersonate="chrome")

if response.status_code == 200:
    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find all elements with the class 'elhe7kv0'
    medal_elements = soup.find_all(class_='elhe7kv0')

    # Initialize lists to store medal data
    countries, golds, silvers, bronzes, totals = [], [], [], [], []

    # Extract and process medal data
    for element in medal_elements:
        try:
            # Extract data using more descriptive class names
            country = element.find(class_='elhe7kv5').text.strip()  # Full country name
            gold_medal = int(element.find_all(class_='e1oix8v91 emotion-srm-81g9w1')[0].text.strip())
            silver_medal = int(element.find_all(class_='e1oix8v91 emotion-srm-81g9w1')[1].text.strip())
            bronze_medal = int(element.find_all(class_='e1oix8v91 emotion-srm-81g9w1')[2].text.strip())
            total_medal = int(element.find(class_='e1oix8v91 emotion-srm-5nhv3o').text.strip())

            # Append data to lists
            countries.append(country)
            golds.append(gold_medal)
            silvers.append(silver_medal)
            bronzes.append(bronze_medal)
            totals.append(total_medal)

        except (AttributeError, IndexError, ValueError) as e:
            # Handle any parsing errors
            st.error(f"{translations[lang_code]['error_parsing']} {e}")

    # Update the last updated time
    st.session_state['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Create a DataFrame from the lists
    full_df = pd.DataFrame({
        'Country': countries,
        'Gold Medals': golds,
        'Silver Medals': silvers,
        'Bronze Medals': bronzes,
        'Total Medals': totals
    })

    # First DataFrame: Sort by number of Gold, then Silver, then Bronze medals
    sorted_by_medals_df = full_df.sort_values(
        by=['Gold Medals', 'Silver Medals', 'Bronze Medals'], 
        ascending=False
    ).reset_index(drop=True)

    # Second DataFrame: Calculate the Weighted Gold Score
    full_df['Weighted Gold Score'] = full_df['Gold Medals'] + full_df['Silver Medals'] / 2 + full_df['Bronze Medals'] / 3

    # Sort by Weighted Gold Score
    sorted_by_weighted_score_df = full_df.sort_values(
        by='Weighted Gold Score', 
        ascending=False
    ).reset_index(drop=True)

    # Calculate ranks in both sorted DataFrames
    sorted_by_medals_df['Rank by Medals'] = sorted_by_medals_df.index + 1
    sorted_by_weighted_score_df['Rank by Weighted Score'] = sorted_by_weighted_score_df.index + 1

    # Merge the two DataFrames on the 'Country' column
    merged_df = pd.merge(
        sorted_by_medals_df[['Country', 'Rank by Medals']],
        sorted_by_weighted_score_df[['Country', 'Rank by Weighted Score']],
        on='Country'
    )

    # Calculate the change in rank
    merged_df['Rank Change'] = merged_df['Rank by Medals'] - merged_df['Rank by Weighted Score']

    # Function to apply conditional styling
    def highlight_rank_change(row):
        if row['Rank Change'] > 0:
            return ['background-color: green'] * len(row)
        elif row['Rank Change'] < 0:
            return ['background-color: red'] * len(row)
        else:
            return [''] * len(row)

    # Apply the styling to the merged DataFrame
    styled_merged_df = merged_df.style.apply(highlight_rank_change, axis=1)

    # Display the DataFrames and explanations in Streamlit
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(translations[lang_code]["sorted_by_medals"])
        st.dataframe(sorted_by_medals_df)

    with col2:
        st.subheader(translations[lang_code]["sorted_by_weighted_score"])
        st.dataframe(sorted_by_weighted_score_df)

    st.subheader(translations[lang_code]["rank_change"])
    st.dataframe(styled_merged_df)

else:
    st.error(f"{translations[lang_code]['failed_retrieve']} {response.status_code}")
