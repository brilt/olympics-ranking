import streamlit as st
from curl_cffi import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

st.set_page_config(
    page_title="Olympics Ranking",
    page_icon="🎖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

with st.sidebar:

    # Initialize session state for last updated time if not already present
    if 'last_updated' not in st.session_state:
        st.session_state['last_updated'] = None

    # Add a button to reload the data
    if st.button("Reload Data"):
        st.rerun()
    # Display the last updated time
    st.info(f"Last Updated {st.session_state['last_updated']}")

    # Explanation of the weighted calculation
    latext = r'''
    ### Explanation of Weighted Gold Score Calculation
    The **Weighted Gold Score** is calculated to provide a more balanced ranking by considering the relative value of each medal type. 
    The formula used is:
    $\text{Weighted Gold Score}=\text{Gold Medals} + \frac{\text{Silver Medals}}{2} + \frac{\text{Bronze Medals}}{3}$.
    '''
    st.info(latext)

# Retrieve the webpage
response = requests.get("https://olympics.com/fr/paris-2024/medailles", impersonate="chrome")

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
            st.error(f"Error parsing element: {e}")

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
        st.subheader("Sorted by Number of Medals")
        st.dataframe(sorted_by_medals_df)

    with col2:
        st.subheader("Sorted by Weighted Gold Score")
        st.dataframe(sorted_by_weighted_score_df)

    st.subheader("Rank Change from Medals to Weighted Score")
    st.dataframe(styled_merged_df)

else:
    st.error(f"Failed to retrieve the webpage. Status code: {response.status_code}")
