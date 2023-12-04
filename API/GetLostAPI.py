from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from typing import List
from pydantic import BaseModel
import pandas as pd
import uvicorn
import logging
from starlette.middleware.cors import CORSMiddleware

app = FastAPI()
#ensure you use this:
# python -m venv venv; venv\Scripts\activate; python3 -m uvicorn GetLostAPI:app --reload
#wont work unless python version is specified.
# Load CSV files into Pandas DataFrames
#having issues reading contents of CSVs
trails_df = pd.read_csv('trails.csv', encoding='latin1')
trail_details_df = pd.read_csv('traildetails.csv', encoding='latin1')
trails_info_df = pd.read_csv('trailsinfo.csv', encoding='latin1')
user_posts_file = "userPosts.csv"
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

#making sure cross origin resource sharing is allowed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this to the appropriate origin in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class UserPostCreate(BaseModel):
    PostId: str
    TrailName: str
    Description: str
    Rating: int

class UserPost(UserPostCreate):
    Photo: str

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

# Create a new user post
@app.post("/user/posts")
async def create_user_post(user_post: dict, file: UploadFile = File(None)):
    try:
        logger.info("Received request to create a new user post")

        # Generate a unique post ID
        user_post_dict = user_post.dict()
        user_post["PostId"] = str(uuid.uuid4())

        if file:
            file_name = f"UserImgs/{file.filename}"
            with open(file_name, "wb") as f:
                f.write(file.file.read())
            user_post["Photo"] = file_name

        with open(user_posts_file, mode="a", newline="") as csvfile:
            fieldnames = ["PostId", "TrailName", "Description", "Rating", "Photo"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writerow(user_post)
            logger.info("User post written to CSV")

        return JSONResponse(content={"message": "User post created successfully"}, status_code=201)
    except Exception as e:
        logger.error(f"Error creating user post: {str(e)}")
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)


# Fetch user posts from CSV
@app.get("/user/posts", response_model=list[dict])
def get_user_posts():
    try:
        user_posts_df = pd.read_csv("userPosts.csv", encoding='utf-8')
        user_posts = user_posts_df.to_dict(orient='records')
        return user_posts
    except Exception as e:
        logging.exception("Error fetching user posts:")
        raise HTTPException(status_code=500, detail="Internal Server Error")    
   
@app.post("/test")
def test_endpoint():
    return {"message": "Test successful"}


#UPDATE
@app.put("/user/posts/{post_id}")
async def update_user_post(
    post_id: int,
    user_post_update: UserPostCreate,  # Assuming a Pydantic model for updating posts
    file: UploadFile = File(None)

):
    logger.debug(f"Existing TrailIds: {user_posts_df['TrailId'].values}")
    try:
        # Load existing user posts from the CSV file
        user_posts_df = pd.read_csv(user_posts_file, encoding='utf-8')

        # Check if the post with the specified ID exists
        if post_id not in user_posts_df['TrailId'].values:
            raise HTTPException(status_code=404, detail="Post not found")
        logger.debug(f"Received post_id: {post_id}")
        # Update the post with the new data
        user_posts_df.loc[user_posts_df['TrailId'] == post_id, 'PostId'] = user_post_update.PostId
        user_posts_df.loc[user_posts_df['TrailId'] == post_id, 'TrailName'] = user_post_update.TrailName
        user_posts_df.loc[user_posts_df['TrailId'] == post_id, 'Description'] = user_post_update.Description
        user_posts_df.loc[user_posts_df['TrailId'] == post_id, 'Rating'] = user_post_update.Rating

        # Handle file upload if a new file is provided
        if file:
            file_name = f"UserImgs/{file.filename}"
            with open(file_name, "wb") as f:
                f.write(file.file.read())
            user_posts_df.loc[user_posts_df['TrailId'] == post_id, 'Photo'] = file_name

        # Save the updated user posts back to the CSV file
        user_posts_df.to_csv(user_posts_file, index=False, encoding='utf-8')

        return JSONResponse(content={"message": "Post updated successfully"}, status_code=200)
    except Exception as e:
        # Log the error for debugging
        logger.error(f"Error updating user post: {str(e)}")
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)

#DELETE
@app.delete("/user/posts/{post_id}")
async def delete_user_post(post_id: int):
    try:
        # Load existing user posts from the CSV file
        user_posts_df = pd.read_csv(user_posts_file, encoding='utf-8')

        # Check if the post with the specified ID exists
        if post_id not in user_posts_df['TrailId'].values:
            raise HTTPException(status_code=404, detail="Post not found")

        # Delete the post with the specified ID
        user_posts_df = user_posts_df[user_posts_df['TrailId'] != post_id]

        # Save the updated user posts back to the CSV file
        user_posts_df.to_csv(user_posts_file, index=False, encoding='utf-8')

        return JSONResponse(content={"message": "Post deleted successfully"}, status_code=200)
    except Exception as e:
        # Log the error for debugging
        logger.error(f"Error deleting user post: {str(e)}")
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)