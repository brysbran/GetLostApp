from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
import pandas as pd

app = FastAPI()
#ensure you use this:
# python -m venv venv; venv\Scripts\activate; python3 -m uvicorn GetLostAPI:app --reload
#wont work unless python version is specified.
# Load CSV files into Pandas DataFrames
#having issues reading contents of CSVs
trails_df = pd.read_csv('trails.csv', encoding='latin1')
trail_details_df = pd.read_csv('traildetails.csv', encoding='latin1')
trails_info_df = pd.read_csv('trailsinfo.csv', encoding='latin1')


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
@app.get("/trails/{state}", response_model=list[dict])
def get_trails_by_state_endpoint(state: str):
    try:
        return get_trails_by_state(state)

    except HTTPException as e:
        # Re-raise HTTPException with the appropriate status code
        raise e
    except Exception as e:
        # Catch other exceptions and return a 500 Internal Server Error
        raise HTTPException(status_code=500, detail=str(e))

# API endpoint to get trail information by ID
@app.get("/trails/{trail_id}/info", response_model=dict)
def read_item(trail_id: int):
    return get_trail_info(trail_id)

# API endpoint to get trail details by ID
@app.get("/trails/{trail_id}/details", response_model=dict)
def get_trail_details_endpoint(trail_id: int):
    try:
        return get_trail_details(trail_id)
    except HTTPException as e:
        # Re-raise HTTPException with the appropriate status code
        raise e
    except Exception as e:
        # Catch other exceptions and return a 500 Internal Server Error
        raise HTTPException(status_code=500, detail=str(e))


# API endpoint to get all trails
@app.get("/trails", response_model=list[dict])
def get_all_trails():
    return trails_df.to_dict(orient='records')

# Function to handle user posts
def handle_user_post(user_post: dict, photo: UploadFile):
    # Validate and process the user's input

    # Convert the user_post dictionary to a DataFrame
    user_post_df = pd.DataFrame([user_post])

    # Save the post details to a CSV file
    with open("user_posts.csv", "a", encoding='utf-8') as f:
        # Append the DataFrame to the CSV file, without writing the header if the file exists
        user_post_df.to_csv(f, header=f.tell() == 0, index=False, encoding='utf-8')

    # Handle photo upload and save the image
    with open(f"uploads/{photo.filename}", "wb") as f:
        f.write(photo.file.read())

    # Return a response, possibly with a success message
    return {"message": "Post created successfully"}

# Endpoint to write post to CSV
@app.post("/user/posts")
async def post_user_experience(user_post: dict, photo: UploadFile = File(...)):
    try:
        print("Write post endpoint called")
        result = handle_user_post(user_post, photo)
        return JSONResponse(content=jsonable_encoder(result), status_code=200)
    except HTTPException as e:
        return JSONResponse(content=jsonable_encoder({"error": str(e)}), status_code=e.status_code)

# Fetch user posts from CSV
@app.get("/user/posts", response_model=list[dict])
def get_user_posts():
    try:
        user_posts_df = pd.read_csv("user_posts.csv", encoding='utf-8')
        user_posts = user_posts_df.to_dict(orient='records')
        return user_posts
    except Exception as e:
        logging.exception("Error fetching user posts:")
        raise HTTPException(status_code=500, detail="Internal Server Error")    