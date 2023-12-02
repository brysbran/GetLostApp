from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
import pandas as pd
import logging
import uvicorn

app = FastAPI()
#ensure you use this:
# python -m venv venv; venv\Scripts\activate; python3 -m uvicorn GetLostAPI:app --reload
#wont work unless python version is specified.
# Load CSV files into Pandas DataFrames
#having issues reading contents of CSVs
trails_df = pd.read_csv('trails.csv', encoding='latin1')
trail_details_df = pd.read_csv('traildetails.csv', encoding='latin1')
trails_info_df = pd.read_csv('trailsinfo.csv', encoding='latin1')

def detect_encoding(file_path):
    encodings_to_try = ['utf-8', 'latin-1']

    for encoding in encodings_to_try:
        try:
            with open(file_path, 'r', encoding=encoding) as file:
                file.read()
            return encoding
        except UnicodeDecodeError:
            pass

    return None

file_path = 'userPosts.csv'
detected_encoding = detect_encoding(file_path)

if detected_encoding:
    print(f"The file is encoded in: {detected_encoding}")
else:
    print("Unable to determine encoding.")


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

# Function to update trail information by ID
def update_trail(trail_id, updated_info):
    # Your logic to update trail information in the data source
    try:
        trails_info_df.loc[trails_info_df['trailID'] == trail_id, ['trailDifficulty', 'trailLength', 'trailRating']] = [
            updated_info['trailDifficulty'], updated_info['trailLength'], updated_info['trailRating']
        ]
        trails_info_df.to_csv('trailsinfo.csv', index=False)
        return get_trail_info(trail_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Function to delete trail by ID
def delete_trail(trail_id):
    # Your logic to delete the trail from the data source
    try:
        trails_info_df.drop(trails_info_df[trails_info_df['trailID'] == trail_id].index, inplace=True)
        trails_info_df.to_csv('trailsinfo.csv', index=False)
        return {"message": f"Trail {trail_id} has been deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# API endpoint to update trail information by ID
@app.put("/trails/{trail_id}/update", response_model=dict)
def update_trail_endpoint(trail_id: int, updated_info: dict):
    try:
        return update_trail(trail_id, updated_info)
    except HTTPException as e:
        # Re-raise HTTPException with the appropriate status code
        raise e

# API endpoint to delete trail by ID
@app.delete("/trails/{trail_id}/delete", response_model=dict)
def delete_trail_endpoint(trail_id: int):
    try:
        return delete_trail(trail_id)
    except HTTPException as e:
        # Re-raise HTTPException with the appropriate status code
        raise e

# Define a Pydantic model for UserPost
class UserPost(BaseModel):
    Description: str
    Rating: int
    TrailName: str
    PhotoPath: str
    
#POST
@app.post("/user/posts")
async def post_user_experience(
    Description: str = Form(...),
    Rating: int = Form(...),
    TrailName: str = Form(...),
    photo: UploadFile = File(..., max_length=None),
):
    try:
        # Process the user's input
        new_post = {
        "description": user_post.get("Description"),
        "postRating": user_post.get("Rating"),
        "trailName": str(TrailName),
        "PhotoPath": f"/API/UserImgs/{photo.filename}",
        }
        print(new_post) 
        new_post_df = pd.DataFrame([new_post])
        print(new_post_df) 
        # Save the post details to a CSV file
        with open("userPosts.csv", "a", encoding='utf-8') as f:
            new_post_df = pd.DataFrame([new_post], columns=["description", "postRating", "trailName", "photoPath"])
            new_post_df.to_csv(f, header=f.tell() == 0, index=False, encoding='utf-8')

        # Handle photo upload and save the image
        with open(f"/API/UserImgs/{photo.filename}", "wb") as f:
            f.write(photo.file.read())

        # Return a response, possibly with a success message
        return {"message": "Post created successfully"}

    except HTTPException as e:
        return JSONResponse(
            content=jsonable_encoder({"error": str(e)}), status_code=e.status_code
        )


# POST endpoint for creating a user post
@app.post("/user/posts")
async def handle_user_post(user_post: UserPost, photo: UploadFile, TrailName: str = Form(...)):
    try:
        # Convert Pydantic model to a dictionary
        new_post = jsonable_encoder(user_post)

        # Add additional data to the dictionary
        new_post["trailName"] = TrailName

        # Convert the dictionary to a DataFrame
        new_post_df = pd.DataFrame([new_post])

        # Save the post details to a CSV file
        with open("userPosts.csv", "a", encoding='utf-8') as f:
            new_post_df.to_csv(f, header=f.tell() == 0, index=False, encoding='utf-8')

        # Handle photo upload and save the image
        with open(f"API/UserImgs/{photo.filename}", "wb") as f:
            f.write(photo.file.read())

        # Return a response, possibly with a success message
        return {"message": "Post created successfully"}

    except Exception as e:
        logging.exception(f"Error creating post: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/user/posts", response_model=list[UserPost])
async def get_user_posts():
    print("Endpoint is called")
    try:
        user_posts_df = pd.read_csv("userPosts.csv", encoding='utf-8')

        # Convert DataFrame to a list of dictionaries
        user_posts_data = user_posts_df.to_dict(orient='records')

        # Create a list to store UserPost instances
        user_posts = []

        # Iterate over each record and create UserPost instance
        for post_data in user_posts_data:
            user_post = UserPost(
                Description=post_data.get('description', ''),
                Rating=post_data.get('postRating', ''),
                TrailName=post_data.get('trailName', ''),
                PhotoPath=post_data.get('photoPath', '')
            )
            user_posts.append(user_post)

        # Log the fetched posts
        print(user_posts)

        return user_posts

    except Exception as e:
        logging.exception("Error fetching user posts:")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    

if __name__ == "main":
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)