# -*- coding: utf-8 -*-
"""
Created on Fri Jan 24 15:44:42 2025

@author: danie
"""

# Import libraries.
import requests  # Internet information requests
from bs4 import BeautifulSoup  # Parsing HTML
import pandas as pd # Enables code to create a sublist using a dataframe


#%%
#SCRAPE
#Fetch HTML content from Taskmaster Fandom Wiki Episode List
url = "https://taskmaster.fandom.com/wiki/Episode_list"
response = requests.get(url).content

#Store content as "parsed_html"
parsed_html = BeautifulSoup(response, "html.parser")

#%%
#PARSE
#Parse tables. Each table in 'tables' is a different TM series.
tables = parsed_html.find_all("table", {"class": "tmtable"})

#Parse series names.
series = parsed_html.find_all("h2")

#%%
#EXTRACT
#Extract series_names.
series_names = []
for s in series:
    span_element = s.find('span', class_='mw-headline')
    if span_element:
        series_name = span_element.text
        series_names.append(series_name)
        
#%%
        
#Function for extracting headers.
def extract_header(table):
    header = table.find('tr', class_='tmtableheader')
    tm_header = [th.text.strip() for th in header.find_all('th')]
    return tm_header

#%%
#Function for extracting rows and episodes
def extract_data(table):
    table_rows = table.find_all('tr')  # Select all rows initially
    rows = []
    for row in table_rows:
        # Exclude rows with specific classes
        if not any(exclude_class in row.get('class', []) for exclude_class in ['tmtableheader', 'tmtabletotal', 'tmtablegrandtotal']):
            cells = row.find_all(['td'])
            row_data = [cell.text.strip() for cell in cells]
            rows.append(row_data)
    return rows

#%%
#Function to ensure inner lists are same length
def modify_nested_list(rows):
    """
    Checks the length of lists within a nested list. If a list has length 6,
    it duplicates the first element of the prior list and inserts it at the
    beginning of the list with length 6.

    Args:
        nested_list: The nested list to modify.

    Returns:
        The modified nested list.
    """

    for i in range(1, len(rows)):  # Start from index 1
        if len(rows[i]) == 6:
            if i > 0 and rows[i - 1]:  # Check if previous list exists and is not empty
                duplicate_element = rows[i - 1][0]
                rows[i].insert(0, duplicate_element)
    return rows

#%%
#STRUCTURE DATA
def create_episode_dict(rows):
    """
    Creates a dictionary from a list of lists, where lists containing "Episode"
    are keys and subsequent lists are the values until another list with "Episode" is reached.

    Args:
        rows: A list of lists extracted from the HTML table.

    Returns:
        episode_dict: A dictionary with episode titles as keys and a list of corresponding rows as values.
    """
    episode_dict = {}
    current_episode = None  # Variable to track the current episode

    for row in rows:
        if any("Episode" in str(cell) for cell in row):  # Check if "Episode" is in any cell
            # Extract episode title (assuming it's the first cell)
            current_episode = row[0]
            episode_dict[current_episode] = []  # Initialize an empty list for this episode
        elif current_episode:  # If we're within an episode block and row is not an episode title
            episode_dict[current_episode].append(row)

    return episode_dict

#%%
#CREATE DF
def dict_to_df(episode_dict, header, series_name):
  """
  Create series dataframe from episode_dict, header, and series_name.
  
  Args:
    episode_dict: Dictionary of episode data.
    header: List of column headers.
    series_name: Name of the series.
  
  Returns:
    df: DataFrame of episode data for series in tidy format.

  """
  episode_dfs = [] #Empty list to store dataframes
  for episode, data in episode_dict.items(): #Iterates through each episode
    episode_df = pd.DataFrame(data, columns=header) #Create df for episode
    episode_df.insert(0, 'Episode', episode) #Episode column
    episode_df.insert(0, 'Series', series_name) #Series column
    episode_dfs.append(episode_df) #Append episode_df to episode_dfs
  # Check if episode_dfs is empty before concatenation
  if episode_dfs:  # Proceed only if episode_dfs is not empty
    df = pd.concat(episode_dfs, ignore_index=True) #Combine episode_dfs list into df
    #Reshape into tiny format
    df_melt = pd.melt(df, id_vars=df.columns[:4], value_vars=df.columns[4:],
                      var_name='Contestant', value_name='Score')
    return df_melt
  else:
    # Handle the case where episode_dfs is empty, e.g., return an empty DataFrame
    return pd.DataFrame(columns=['Series', 'Episode', 'Task', 'Description', 'Contestant', 'Score'])

#%%
#COMBINE
# Initialize an empty list to store the dataframes
final_df = []

# Loop through each table in the 'tables' list
for i in range(len(tables)):
    # Extract header and rows for the current table
    header = extract_header(tables[i])
    rows = extract_data(tables[i])
    rows2 = modify_nested_list(rows)

    # Create the episode dictionary and convert it to a dataframe
    episode_dict = create_episode_dict(rows2)
    df = dict_to_df(episode_dict, header, series_names[i])

    # Append the dataframe to the final list
    final_df.append(df)

# Concatenate all dataframes in the final list into a single dataframe
final_df = pd.concat(final_df, ignore_index=True)

# Display the final dataframe
final_df

#%%
#SAVE
final_df.to_csv('tm_episodes.csv', index=False)