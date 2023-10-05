import requests
import json
import csv
url = "https://zillow56.p.rapidapi.com/search"
from datetime import datetime
import sqlite3
import pandas as pd

def searchZillow():
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    # filename = f"data_{timestamp}.txt"
    # querystring = {"location":"seattle, wa","status":"recentlySold"}
    #
    # headers = {
    #     "X-RapidAPI-Key": "ade2517b07msha8401ba0c4f1ac2p189937jsn03f85bb20c18",
    #     "X-RapidAPI-Host": "zillow56.p.rapidapi.com"
    # }
    #
    # response = requests.get(url, headers=headers, params=querystring)
    #
    # responseobject = response.json()

    # with open(filename, "w") as file:
    #     json.dump(responseobject, file)

    with open('data.txt', "r") as file:
        responseobject = json.load(file)

    results = responseobject['results']
    all_fields = set()
    for result in results:
        all_fields.update(result.keys())

    # Step 2 & 3: Use these fields as the CSV headers and write each result to the CSV.
    with open('data.csv', 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=all_fields)
        writer.writeheader()
        for row in results:
            writer.writerow(row)
    return responseobject

def loadcsv():
    with open('data.csv', 'r') as file:
        reader = csv.DictReader(file)
        data = list(reader)
    return data

def addHomesToDB():
    csv_file_path = 'path_to_your_csv_file.csv'

    # Connect to the SQLite database
    conn = sqlite3.connect('listings.db')
    cursor = conn.cursor()

    # Open the CSV file and read its contents
    with open(csv_file_path, 'r') as csv_file:
        csv_reader = csv.reader(csv_file)

        # Skip header (if it exists)
        next(csv_reader)

        # Insert each row into the database
        for row in csv_reader:
            # Assuming the CSV columns match the database table columns
            cursor.execute("INSERT INTO Listing (api_id, added_on) VALUES (?, ?)", (row[0], row[1]))

    # Commit the changes and close the connection
    conn.commit()
    conn.close()