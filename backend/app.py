import os
from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from flask_cors import CORS
from dotenv import load_dotenv
import anthropic # Import the anthropic library
import json # To parse potential JSON in Claude's response
import requests # Import requests library
from bson.objectid import ObjectId # Needed for potential future lookups by ID
from datetime import datetime # Added for timestamp
import traceback # Import traceback
from pymongo import errors # Import errors module

load_dotenv() # Load environment variables from .env file

app = Flask(__name__)
CORS(app) # Enable CORS for all routes

# --- Configuration ---
app.config["MONGO_URI"] = os.getenv("MONGO_URI")
app.config["ANTHROPIC_API_KEY"] = os.getenv("ANTHROPIC_API_KEY")
app.config["BRAVE_SEARCH_API_KEY"] = os.getenv("BRAVE_SEARCH_API_KEY") # Load Brave Key

if not app.config["MONGO_URI"]:
    raise ValueError("No MONGO_URI set for Flask application")
if not app.config["ANTHROPIC_API_KEY"]:
    raise ValueError("No ANTHROPIC_API_KEY set for Flask application")
# Note: Brave key is optional for now, the function will handle its absence

mongo = PyMongo(app)
# Initialize Anthropic Client
anthropic_client = None # Initialize as None
try:
    api_key_loaded = app.config.get("ANTHROPIC_API_KEY")
    if api_key_loaded:
        print(f"Attempting to initialize Anthropic client with key type: {type(api_key_loaded)}, starting with: {api_key_loaded[:5]}...")
        anthropic_client = anthropic.Anthropic(api_key=api_key_loaded)
        print("Anthropic client initialized successfully.") # Add success log
    else:
        print("Error: ANTHROPIC_API_KEY not found in app config.")

except Exception as e:
    print("--- FATAL: Error initializing Anthropic client --- ") # Make error more visible
    print(f"Error Type: {type(e).__name__}")
    print(f"Error Args: {e.args}")
    print("Traceback:")
    traceback.print_exc() # Print full traceback
    print("--- End Anthropic Init Error ---")
    anthropic_client = None # Ensure it's None on error

# --- Routes ---
@app.route('/')
def home():
    return "LinkedIn Style Syncer Backend"

# Style Analysis & Auto-Save Endpoint
@app.route('/api/analyze-style', methods=['POST'])
def analyze_and_save_style(): # Renamed function for clarity
    if not anthropic_client:
         return jsonify({"error": "Anthropic client not initialized. Check API key."}), 500

    # 1. Get posts from request body
    data = request.get_json()
    posts_text = data.get('posts_text')
    if not posts_text or len(posts_text.strip()) < 100: # Basic validation
        return jsonify({"error": "Insufficient post text provided for analysis (min 100 chars recommended)."}), 400

    # 2. Send to Anthropic for analysis AND name suggestion
    try:
        # Prompt for Messages API (no HUMAN/AI prompts needed explicitly)
        analysis_prompt = f"""Analyze the following LinkedIn posts provided below to determine the author's writing style. Extract the key stylistic elements and provide the analysis as a JSON object.

The JSON object should include keys for:
- overall_tone (e.g., Formal, Informal, Enthusiastic, Analytical, Inspirational, Humorous)
- key_themes (list of strings, e.g., ["Technology", "Leadership", "Marketing"])
- common_keywords (list of strings)
- sentence_structure (e.g., "short and punchy", "complex sentences", "mix of short and long")
- emoji_usage (e.g., "frequent", "occasional", "rare", "none", specific common emojis)
- common_cta (common call-to-actions used, e.g., "Link in comments", "DM me", "Visit website", or null if none consistent)
- perspective (e.g., "First-person", "Third-person")
- style_name (Suggest a short, descriptive name for this style based on the analysis, e.g., "Professional Tech Insights", "Casual Startup Banter", "Inspirational Leadership Voice")

Please ensure the output is ONLY the JSON object, without any introductory text or explanation.

Here are the posts:
--- START POSTS ---
{posts_text}
--- END POSTS ---
"""

        # Use the Messages API
        message = anthropic_client.messages.create(
            model="claude-3-7-sonnet-20250219", # Use specific Sonnet 3.7 model ID
            max_tokens=1000,
            temperature=0.1,
            messages=[
                {
                    "role": "user",
                    "content": analysis_prompt
                }
            ]
        )
        # Extract text from Messages API response
        analysis_text = message.content[0].text.strip()

        # Parse JSON (using existing robust logic)
        if analysis_text.startswith("```json"):
            analysis_text = analysis_text.strip("```json").strip("`").strip()
        elif analysis_text.startswith("{") and analysis_text.endswith("}"):
            pass # Looks like JSON already
        else:
            json_start = analysis_text.find('{')
            json_end = analysis_text.rfind('}')
            if json_start != -1 and json_end != -1 and json_end > json_start:
                analysis_text = analysis_text[json_start:json_end+1]
            else:
                 print(f"Warning: Could not reliably extract JSON from Anthropic response. Raw response: {analysis_text}")
                 return jsonify({"error": "Could not extract JSON analysis from AI model response.", "raw_output": analysis_text}), 500

        try:
            analysis_result = json.loads(analysis_text)
        except json.JSONDecodeError as e:
             print(f"Warning: Could not parse extracted Anthropic response as JSON. Parse error: {e}. Extracted text: {analysis_text}")
             return jsonify({"error": "Failed to parse analysis from AI model", "raw_output": analysis_text}), 500

        # --- Auto-Save Logic ---
        style_name = analysis_result.get('style_name', 'Unnamed Style') # Use suggested name or default

        styles_collection = mongo.db.styles
        style_doc = {
            # "user_id": user_id, # Add later
            "name": style_name.strip(),
            "analysis": analysis_result, # Store the full analysis
            "created_at": datetime.utcnow()
        }
        insert_result = styles_collection.insert_one(style_doc)

        if not insert_result.inserted_id:
             # Log error, but maybe still return analysis?
             print(f"Error: Failed to auto-save style '{style_name}' to database after analysis.")
             # Decide if we should return an error or just the analysis without save confirmation
             # Returning analysis but with a warning for now:
             analysis_result['save_warning'] = 'Style analysis complete, but failed to auto-save.'
             return jsonify(analysis_result), 200 # 200 OK, but with warning

        saved_style_id = str(insert_result.inserted_id)
        print(f"Style '{style_name}' analyzed and auto-saved successfully with ID: {saved_style_id}")
        # --- End Auto-Save ---

        # 3. Return analysis result AND save confirmation
        return jsonify({
            "message": f"Style analyzed and saved as '{style_name}'!",
            "style_id": saved_style_id,
            "style_name": style_name, # Return the name used for saving
            "analysis": analysis_result # Return the full analysis object
            }), 200 # 200 OK since analysis and save (mostly) succeeded

    except anthropic.APIConnectionError as e:
        print(f"Anthropic API connection error: {e}")
        return jsonify({"error": "Failed to connect to Anthropic API"}), 503 # Service Unavailable
    except anthropic.RateLimitError as e:
        print(f"Anthropic API rate limit exceeded: {e}")
        return jsonify({"error": "Rate limit exceeded. Please try again later."}), 429 # Too Many Requests
    except anthropic.APIStatusError as e:
        print(f"Anthropic API status error: {e}")
        return jsonify({"error": f"Anthropic API error: {e.status_code} {e.response}"}), 500
    except Exception as e:
        # Catch-all for other unexpected errors (includes DB errors during save)
        print(f"Unexpected error during style analysis or auto-save: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "An unexpected error occurred during style analysis or auto-save."}), 500


# Style Listing Endpoint (GET only)
# POST logic moved to analyze_and_save_style
@app.route('/api/styles', methods=['GET'])
def handle_styles_get(): # Renamed function
    if request.method == 'GET':
        # --- GET logic for listing styles ---
        try:
            styles_collection = mongo.db.styles
            # TODO: Add filter for user_id when authentication is implemented
            all_styles = list(styles_collection.find({}, {'_id': 1, 'name': 1}))
            for style in all_styles:
                style['_id'] = str(style['_id']) # Convert ObjectId to string
            return jsonify(all_styles)

        except Exception as e:
            print(f"Error fetching styles from MongoDB: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": "An unexpected error occurred while fetching styles."}), 500
        # --- End GET logic ---

# Style Deletion Endpoint
@app.route('/api/styles/<string:style_id>', methods=['DELETE'])
def delete_style(style_id):
    try:
        styles_collection = mongo.db.styles
        # Convert the string ID from the URL to a MongoDB ObjectId
        style_object_id = ObjectId(style_id)

        # Attempt to delete the document
        delete_result = styles_collection.delete_one({"_id": style_object_id})

        # Check if a document was actually deleted
        if delete_result.deleted_count == 1:
            print(f"Successfully deleted style with ID: {style_id}")
            return jsonify({"message": "Style deleted successfully"}), 200
        else:
            # No document found with that ID
            print(f"Attempted to delete style ID: {style_id}, but it was not found.")
            return jsonify({"error": "Style not found"}), 404

    except errors.InvalidId: # Catch BSON errors if the ID format is wrong
        print(f"Invalid ObjectId format provided for deletion: {style_id}")
        return jsonify({"error": "Invalid style ID format"}), 400
    except Exception as e:
        print(f"Error deleting style {style_id} from MongoDB: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "An unexpected error occurred while deleting the style."}), 500

# --- Helper Function for Brave Search (Real Implementation) ---
def perform_brave_search(query, count=3):
    """Calls the Brave Search API and returns results or None on error."""
    api_key = app.config.get("BRAVE_SEARCH_API_KEY")
    if not api_key:
        print("Warning: BRAVE_SEARCH_API_KEY not set. Skipping web search.")
        return None

    url = "https://api.search.brave.com/res/v1/web/search" # Corrected endpoint
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": api_key # Use X-Subscription-Token header
    }
    params = {
        "q": query,
        "count": count
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10) # Added timeout
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

        data = response.json()
        # Adjust based on Brave's actual response structure - often under 'web' -> 'results'
        results = data.get('web', {}).get('results')

        if results:
            # Return simplified list of title/description
            return [
                {"title": r.get('title'), "description": r.get('description')}
                for r in results if r.get('title') and r.get('description')
                ]
        else:
            print(f"Brave Search returned no results under 'web.results' for query: {query}")
            print(f"Raw response sample: {str(data)[:200]}") # Log sample of response
            return None

    except requests.exceptions.RequestException as e:
        print(f"Error during Brave Search API call for query '{query}': {e}")
        return None
    except Exception as e:
        print(f"Unexpected error processing Brave Search results for query '{query}': {e}")
        return None

# --- Post Generation Endpoint (Modified to use real search) ---
@app.route('/api/generate-post', methods=['POST'])
def generate_post():
    if not anthropic_client:
         return jsonify({"error": "Anthropic client not initialized. Check API key."}), 500

    # 1. Get inputs (including optional subjects/angles)
    data = request.get_json()
    style_id = data.get('style_id')
    topic = data.get('topic')
    key_points = data.get('key_points')
    cta = data.get('cta')
    # New optional input for variations
    subjects_or_angles = data.get('subjects_or_angles', []) # Expect a list of strings
    if isinstance(subjects_or_angles, str): # Handle if a single string is passed
        subjects_or_angles = [subjects_or_angles] if subjects_or_angles.strip() else []

    # Basic validation
    if not style_id or not topic or not key_points:
        return jsonify({"error": "Missing required fields (style_id, topic, key_points)"}), 400

    try:
        # 2. Retrieve style profile (no changes here)
        styles_collection = mongo.db.styles
        style_object_id = ObjectId(style_id)
        style_profile = styles_collection.find_one({"_id": style_object_id})
        if not style_profile:
            return jsonify({"error": "Style not found"}), 404
        style_analysis = style_profile.get('analysis', {})

        # --- Web Search & Multi-Generation Logic ---
        generated_drafts = []
        search_context_base = f"Topic: {topic}. Key Points: {key_points}. "

        # Determine search queries/angles for variations
        angles_to_explore = subjects_or_angles if subjects_or_angles else [topic] # Default to topic if no angles
        max_drafts = 3 # Limit the number of generated drafts

        for i, angle in enumerate(angles_to_explore):
            if len(generated_drafts) >= max_drafts:
                break

            print(f"Exploring angle {i+1}: {angle}")
            search_query = f"{topic} {angle}"

            # Call the REAL search function
            search_results = perform_brave_search(search_query, count=3)

            # --- Add Logging for Search Results ---
            print(f"--- Search Results for '{search_query}': ---")
            print(json.dumps(search_results, indent=2) if search_results else "None")
            print("-------------------------------------")
            # --- End Logging ---

            search_summary = "No specific web search results available for this angle." # Default
            if search_results:
                search_summary = "\n\nRelevant Web Search Snippets:\n"
                for res in search_results:
                    search_summary += f"- Title: {res.get('title', 'N/A')}\n  Snippet: {res.get('description', 'N/A')}\n"

            # 3. Construct prompt for Anthropic API (incorporating search results)
            # --- Prompt Refinement ---
            simplified_topic = topic # Use the user's topic directly here
            simplified_key_points = key_points # Use the user's points directly here

            # Construct the user message content for Messages API - More general instructions
            generation_prompt_content = f"""You are an AI assistant helping a user write a LinkedIn post draft based on their established writing style, the provided requirements, and relevant web search results.

User's Writing Style Analysis:
<style_analysis>
{json.dumps(style_analysis, indent=2)}
</style_analysis>

Post Requirements:
- **Main Topic:** {simplified_topic}
- **Key Points User Wants to Include:**
{simplified_key_points}
- **Specific Angle/Focus for this draft:** {angle}
"""
            if cta:
                generation_prompt_content += f"- **Desired Call-to-Action:** {cta}\n"

            # Add Search Context AFTER requirements
            generation_prompt_content += "\n" # Add separation
            generation_prompt_content += search_summary # Add search summary

            # Remove the explicit style instructions section
            # The model should infer style from the <style_analysis> block.

            # Final Instruction with guidance on using search context and angle
            generation_prompt_content += f"""\n**Final Instruction:**
- Write a LinkedIn post draft that adheres to the User's Writing Style Analysis provided above.
- Focus the content on the angle: '{angle}'.
- Integrate relevant information or viewpoints found in the 'Relevant Web Search Snippets' provided above into the discussion for this angle.
- Generate only the text of the LinkedIn post draft itself, without any extra commentary or preamble.
"""
            # --- End Prompt Refinement ---

            # --- Logging (remains the same) ---
            print(f"--- Prompt Content for Anthropic (Angle: '{angle}'): ---") # Adjusted log label slightly
            print(generation_prompt_content)
            print("-------------------------------------------------------------")
            # --- End Logging ---

            # 4. Send prompt to Anthropic using Messages API
            try:
                message = anthropic_client.messages.create(
                    model="claude-3-7-sonnet-20250219", # Use specific Sonnet 3.7 model ID
                    max_tokens=1500, # Allow for longer posts
                    temperature=0.75, # Slightly higher temp for variation
                    messages=[
                        {
                            "role": "user",
                            "content": generation_prompt_content
                        }
                    ]
                )
                # Extract text from Messages API response
                generated_post = message.content[0].text.strip()

                if generated_post:
                    generated_drafts.append(generated_post)
                    print(f"--- Draft generated for angle: {angle} ---")
                else:
                     print(f"--- Warning: Empty draft generated for angle: {angle} ---")
            except Exception as api_err:
                print(f"Error generating draft for angle '{angle}': {api_err}")
        # --- End Loop ---

        # 5. Return collected drafts
        if not generated_drafts:
             return jsonify({"error": "Failed to generate any drafts. Check inputs or logs."}), 500

        return jsonify({"generated_posts": generated_drafts})

    except ValueError as e:
        print(f"Invalid style ID format: {e}")
        return jsonify({"error": "Invalid style ID format"}), 400
    except Exception as e:
        print(f"Unexpected outer error during post generation: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "An unexpected error occurred during post generation."}), 500

# --- Draft Endpoints ---

# Save New Draft
@app.route('/api/drafts', methods=['POST'])
def save_draft():
    data = request.get_json()
    draft_text = data.get('draft_text')
    # Optional context (add more fields if needed)
    style_id = data.get('style_id')
    topic = data.get('topic')

    if not draft_text:
        return jsonify({"error": "Missing draft_text"}), 400

    try:
        drafts_collection = mongo.db.drafts # Use 'drafts' collection
        draft_doc = {
            # "user_id": user_id, # Add later
            "draft_text": draft_text,
            "style_id": style_id, # Store reference to style used
            "topic": topic, # Store original topic for context
            "created_at": datetime.utcnow()
        }
        insert_result = drafts_collection.insert_one(draft_doc)

        if not insert_result.inserted_id:
             raise Exception("Failed to insert draft into database.")

        saved_draft_id = str(insert_result.inserted_id)
        print(f"Draft saved successfully with ID: {saved_draft_id}")
        return jsonify({
            "message": "Draft saved successfully!",
            "draft_id": saved_draft_id
            }), 201

    except Exception as e:
        print(f"Error saving draft to MongoDB: {e}")
        traceback.print_exc()
        return jsonify({"error": "An unexpected error occurred while saving the draft."}), 500

# List Saved Drafts
@app.route('/api/drafts', methods=['GET'])
def get_drafts():
    try:
        drafts_collection = mongo.db.drafts
        # TODO: Add user filtering later
        # Fetch necessary fields - maybe limit text length for list view?
        all_drafts = list(drafts_collection.find({}, {
            '_id': 1,
            'draft_text': 1, # Fetch full text for now
            'topic': 1,
            'created_at': 1
        }).sort("created_at", -1)) # Sort by newest first

        for draft in all_drafts:
            draft['_id'] = str(draft['_id']) # Convert ObjectId
            # Explicitly format datetime to ISO 8601 string for reliable JS parsing
            if 'created_at' in draft and isinstance(draft['created_at'], datetime):
                draft['created_at'] = draft['created_at'].isoformat() + 'Z' # Add Z to indicate UTC

        return jsonify(all_drafts)

    except Exception as e:
        print(f"Error fetching drafts from MongoDB: {e}")
        traceback.print_exc()
        return jsonify({"error": "An unexpected error occurred while fetching drafts."}), 500

# Delete Saved Draft
@app.route('/api/drafts/<string:draft_id>', methods=['DELETE'])
def delete_draft(draft_id):
    try:
        drafts_collection = mongo.db.drafts
        draft_object_id = ObjectId(draft_id)

        delete_result = drafts_collection.delete_one({"_id": draft_object_id})

        if delete_result.deleted_count == 1:
            print(f"Successfully deleted draft with ID: {draft_id}")
            return jsonify({"message": "Draft deleted successfully"}), 200
        else:
            print(f"Attempted to delete draft ID: {draft_id}, but it was not found.")
            return jsonify({"error": "Draft not found"}), 404

    except errors.InvalidId:
        print(f"Invalid ObjectId format provided for draft deletion: {draft_id}")
        return jsonify({"error": "Invalid draft ID format"}), 400
    except Exception as e:
        print(f"Error deleting draft {draft_id} from MongoDB: {e}")
        traceback.print_exc()
        return jsonify({"error": "An unexpected error occurred while deleting the draft."}), 500

# --- Main Execution ---
if __name__ == '__main__':
    # Use PORT environment variable if available, otherwise default to 5001
    # to avoid conflicts with React's default port 5173
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=True, port=port)
