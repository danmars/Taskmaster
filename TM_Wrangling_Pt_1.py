# -*- coding: utf-8 -*-
"""
Created on Sun Jan 26 12:15:17 2025

@author: danie
"""

#Import libraries
import pandas as pd
import numpy as np
import re

#%%
#Load dataset
df = pd.read_csv('tm_episodes.csv')

#Summary
df.info()

#Create a copy
tmdata = df.copy()

#%%
## HANDLING MISSING VALUES - 'DESCRIPTION'
#Replace '-' with NA
tmdata['Description'] = tmdata['Description'].replace('-', np.nan)

#Replace blank values in 'Description' with 'Task'
tmdata['Description'] = tmdata['Description'].fillna(tmdata['Task'])

tmdata.info()

#%%
## CLEANING 'TASK' COLUMN
#Check length of values in 'Task' column
unique_length = tmdata['Task'].str.len().unique()
print(unique_length)

#Check values with length =<2
filtered_tmdata = tmdata[tmdata['Task'].astype(str).str.len() <= 2]

# Get the values from the 'Task' column of the filtered DataFrame
task_values = filtered_tmdata['Task'].tolist()

# Print the values
print(task_values)

#Remove duplicates in task_values
task_values_clean = list(set(task_values))

#If values in 'Task' are not in 'task_values_clean' then replace with NA
task_mask = ~tmdata['Task'].isin(task_values_clean)

# Use the mask to replace those values with NaN
tmdata.loc[task_mask, 'Task'] = np.nan

tmdata.info()

#Forward fill
tmdata['Task'] = tmdata['Task'].fillna(method='ffill')

tmdata.info()

#%%
## CLEANING 'SCORE' COLUMN
#Create a copy
tm_data = tmdata.copy()

#Function to remove citations from score column
def clean_score(score):
       match = re.match(r"([-]?\d+)", str(score))  # Match an optional "-" followed by one or more digits
       if match:
           return int(match.group(1))  # Convert the extracted part to an integer
       else:
           return score  # If no match, return the original value (e.g., for NaNs)

#Apply function
tm_data['Score'] = tm_data['Score'].apply(clean_score)

#Replace weird values with placeholders
tm_data['Score'] = tm_data['Score'].replace({'✔': 'W', '✘': 'L', '–': 'NP', '-': 'NP'})

#Check
tm_data['Score'].unique()

#Summary - missing score values
tm_data.info()

#Create binary columns for DQ, Tiebreaker, Participated.
tm_data['Disqualified'] = tm_data['Score'].apply(lambda x: 1 if x == 'DQ' else 0)
tm_data['Tiebreaker'] = tm_data['Score'].apply(lambda x: 1 if x == 'W' else 0)
tm_data['Participated'] = tm_data['Score'].apply(lambda x: 0 if x == 'NP' else 1)

#Replace special values with 0
tm_data['Score'] = tm_data['Score'].replace({'W': 0, 'L': 0, 'NP': 0, 'DQ': 0})

#%%
## Handling blanks and multi-part tasks
row_merge = ['Series', 'Episode', 'Task', 'Contestant', 'Tiebreaker']
tm_data2 = tm_data.groupby(row_merge).agg({'Score': 'sum', 'Description': '/ '.join, 'Disqualified': 'max', 'Participated': 'min'}).reset_index()

#Reorganize columns
tm_data2 = tm_data2.iloc[:, [0, 1, 2, 6, 3, 5, 4, 7, 8]]

#Summary
tm_data2.info()

#%%
tm_data2.to_csv('tm_episodes_clean.csv', index=True)
