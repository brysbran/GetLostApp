'''

import sqlite3
import csv
# ... rest of the script ...

# Connect to the SQLite database
conn = sqlite3.connect('trailsdb.db')  # Replace 'your_database.db' with your actual database file

# Create a cursor object to execute SQL queries
cursor = conn.cursor()

# Execute a SELECT query to fetch data from a table (replace 'your_table' with your actual table name)
cursor.execute('SELECT * FROM traildetails')

# Fetch all rows from the query result
rows = cursor.fetchall()

# Close the cursor and database connection
cursor.close()
conn.close()

# Specify the CSV file name (replace 'output.csv' with your desired file name)
csv_file = 'traildetails.csv'

# Open the CSV file in write mode
with open(csv_file, 'w', newline='') as file:
    # Create a CSV writer object
    csv_writer = csv.writer(file)

    # Write the header (column names) to the CSV file
    csv_writer.writerow([description[0] for description in cursor.description])

    # Write the rows to the CSV file
    csv_writer.writerows(rows)

print(f'Data has been exported to {csv_file}')

'''
import pandas as pd

# Specify the file paths
file1_path = 'trails.csv'
file2_path = 'trailsinfo.csv'
file3_path = 'traildetails.csv'

# Read CSV files into pandas DataFrames
df1 = pd.read_csv(file1_path, encoding='utf-8')
df2 = pd.read_csv(file2_path, encoding='utf-8')
df3 = pd.read_csv(file3_path, encoding='utf-8')

# Merge DataFrames based on the 'id' column
# Adjust the 'on' parameter based on your actual column name
merged_df = pd.merge(df1, df2, on='id').merge(df3, on='id')

# Save the merged DataFrame to a new CSV file
merged_df.to_csv('completetrails.csv', index=False)

print('Merged data has been saved to merged_output.csv')
