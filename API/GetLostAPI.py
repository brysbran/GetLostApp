from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import pandas as pd

app = FastAPI()

# Load CSV files into Pandas DataFrames
trails_df = pd.read_csv('trails.csv')
trail_details_df = pd.read_csv('traildetails.csv')
trails_info_df = pd.read_csv('trailsinfo.csv')

# Function to get trail details by ID
def get_trail_details(trail_id):
    trail_details = trail_details_df.loc[trail_details_df['trailID'] == trail_id]
    if trail_details.empty:
        raise HTTPException(status_code=404, detail="Trail details not found")
    return trail_details.to_dict(orient='records')[0]

# Function to get trail information by ID
def get_trail_info(trail_id):
    trail_info = trails_info_df.loc[trails_info_df['trailID'] == trail_id]
    if trail_info.empty:
        raise HTTPException(status_code=404, detail="Trail information not found")
    return trail_info.to_dict(orient='records')[0]

# Function to get trails by state
def get_trails_by_state(state):
    trails_by_state = trails_df.loc[trails_df['trailState'] == state]
    if trails_by_state.empty:
        raise HTTPException(status_code=404, detail=f"No trails found in state {state}")
    return trails_by_state.to_dict(orient='records')

# API endpoint to get trails by state
@app.get("/trails/{state}", response_model=dict)
def get_trails_by_state_endpoint(state: str):
    return get_trails_by_state(state)

# API endpoint to get trail information by ID
@app.get("/trails/{trail_id}/info", response_model=dict)
def read_item(trail_id: int):
    return get_trail_info(trail_id)

"""# API endpoint to get trail by ID
@app.get("/trails/{trail_id}", response_model=dict)
def read_item(trail_id: int):
    return get_trail(trail_id)"""

# API endpoint to get all trails
@app.get("/trails", response_model=dict)
def get_all_trails():
    return trails_df.to_dict(orient='records')

# Additional API endpoints can be added based on your requirements
