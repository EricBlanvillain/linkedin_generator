import pytest
from flask import url_for
import json
from unittest.mock import MagicMock # For creating mock objects
from bson.objectid import ObjectId # Import ObjectId for mocking DB find_one
from datetime import datetime # Import datetime for mocking DB find_one

# Basic test to check if the app loads and the root route works
def test_home_route(client):
    """Test the root route."""
    res = client.get(url_for('home'))
    assert res.status_code == 200
    assert b"LinkedIn Style Syncer Backend" in res.data

# Test for analyze_and_save_style endpoint
def test_analyze_style_success(client, mocker):
    """Test successful style analysis and auto-save."""
    # 1. Mock external dependencies
    # Mock Anthropic API response
    mock_completion = MagicMock()
    mock_completion.completion = json.dumps({
        "overall_tone": "Mock Tone",
        "key_themes": ["Mocking", "Testing"],
        "common_keywords": ["mock", "test", "assert"],
        "sentence_structure": "mock structure",
        "emoji_usage": "none",
        "common_cta": None,
        "perspective": "third-person",
        "style_name": "Mocked Test Style"
    })
    mocker.patch('app.anthropic_client.completions.create', return_value=mock_completion)

    # --- Revised DB Mocking ---
    # Mock MongoDB insert_one result object
    mock_insert_result = MagicMock()
    mock_insert_result.inserted_id = "mock_db_id_123"

    # Create a mock for the 'styles' collection
    mock_styles_collection = MagicMock()
    mock_styles_collection.insert_one.return_value = mock_insert_result

    # Create a mock for the 'db' object
    mock_db = MagicMock()
    # Set the 'styles' attribute on the mock db to be our mock collection
    mock_db.styles = mock_styles_collection

    # Patch the 'db' attribute of the mongo object in the app module
    mocker.patch('app.mongo.db', mock_db)
    # --- End Revised DB Mocking ---

    # 2. Prepare request data
    test_posts = "This is post 1. " * 10 # Ensure > 100 chars
    request_data = {"posts_text": test_posts}

    # 3. Make the request
    res = client.post(url_for('analyze_and_save_style'), json=request_data)

    # 4. Assertions
    assert res.status_code == 200
    response_data = res.get_json()
    assert response_data is not None
    assert "message" in response_data
    assert response_data['message'] == "Style analyzed and saved as 'Mocked Test Style'!"
    # Check against the ID we set on the mock insert result
    assert response_data['style_id'] == "mock_db_id_123"
    assert response_data['style_name'] == "Mocked Test Style"
    assert "analysis" in response_data
    assert response_data['analysis']['overall_tone'] == "Mock Tone"
    assert response_data['analysis']['style_name'] == "Mocked Test Style"

    # Check if the insert_one method on our mock collection was called
    mock_styles_collection.insert_one.assert_called_once()
    call_args, _ = mock_styles_collection.insert_one.call_args
    inserted_doc = call_args[0]
    assert inserted_doc['name'] == 'Mocked Test Style'
    assert inserted_doc['analysis']['overall_tone'] == 'Mock Tone'


def test_analyze_style_insufficient_text(client):
    """Test analyze style with insufficient text."""
    request_data = {"posts_text": "Too short"}
    res = client.post(url_for('analyze_and_save_style'), json=request_data)
    assert res.status_code == 400
    response_data = res.get_json()
    assert "error" in response_data
    assert "Insufficient post text" in response_data['error']

# TODO: Add tests for:
# - Analyze style with Anthropic API error (mock create to raise exception)
# - Analyze style with DB insert error (mock insert_one to raise exception)
# - /api/styles (GET) - Requires setting up test data in DB or mocking find()
# - /api/generate-post (POST) - Requires mocking Anthropic/Brave and DB find_one()

def test_generate_post_success(client, mocker):
    """Test successful post generation with Brave search and multiple angles."""
    # 1. Mock Dependencies
    # Mock DB find_one to return a specific style
    mock_style_id = "67f3917fd2cccab061470337" # Use a valid ObjectId format string
    mock_style_doc = {
        "_id": ObjectId(mock_style_id),
        "name": "Test Style for Gen",
        "analysis": {
            "overall_tone": "Analytical",
            "key_themes": ["AI", "Testing"],
            "common_keywords": ["mock", "generate", "test"],
            "sentence_structure": "complex",
            "emoji_usage": "rare",
            "common_cta": "Check the docs",
            "perspective": "first-person",
            "style_name": "Test Style for Gen" # Ensure name is present
        },
        "created_at": datetime.utcnow()
    }
    # Patch find_one on the mock collection within the mocked db
    # Reuse the mocking strategy from the successful analyze test
    mock_styles_collection_gen = MagicMock()
    mock_styles_collection_gen.find_one.return_value = mock_style_doc
    mock_db_gen = MagicMock()
    mock_db_gen.styles = mock_styles_collection_gen
    mocker.patch('app.mongo.db', mock_db_gen)

    # Mock Brave Search
    mock_search_results_angle1 = [{"title": "Brave Result A", "description": "Snippet A for angle 1"}]
    mock_search_results_angle2 = [{"title": "Brave Result B", "description": "Snippet B for angle 2"}]
    # Use side_effect to return different results based on query
    def brave_side_effect(*args, **kwargs):
        query = kwargs.get('query', args[0] if args else '')
        if "Angle 1" in query:
            return mock_search_results_angle1
        elif "Angle 2" in query:
            return mock_search_results_angle2
        else:
            return []
    mock_brave_search = mocker.patch('app.perform_brave_search', side_effect=brave_side_effect)

    # Mock Anthropic create (to return different posts for different calls)
    mock_completion1 = MagicMock()
    mock_completion1.completion = "Generated Post Draft 1 for Angle 1."
    mock_completion2 = MagicMock()
    mock_completion2.completion = "Generated Post Draft 2 for Angle 2."
    mock_anthropic_create = mocker.patch('app.anthropic_client.completions.create', side_effect=[mock_completion1, mock_completion2])

    # 2. Prepare request data
    request_data = {
        "style_id": mock_style_id,
        "topic": "Main Topic: Testing LLMs",
        "key_points": "- Mocking is essential\n- Verify API calls",
        "cta": "Read the tests",
        "subjects_or_angles": ["Angle 1: Integration", "Angle 2: Quality Challenges"]
    }

    # 3. Make the request
    res = client.post(url_for('generate_post'), json=request_data)

    # 4. Assertions
    assert res.status_code == 200
    response_data = res.get_json()
    assert response_data is not None
    assert "generated_posts" in response_data
    assert len(response_data["generated_posts"]) == 2 # Expect 2 drafts for 2 angles
    assert response_data["generated_posts"][0] == "Generated Post Draft 1 for Angle 1."
    assert response_data["generated_posts"][1] == "Generated Post Draft 2 for Angle 2."

    # Assert mocks were called correctly
    mock_styles_collection_gen.find_one.assert_called_once_with({"_id": ObjectId(mock_style_id)})
    assert mock_brave_search.call_count == 2
    # Check arguments passed to brave search using positional arg for query
    mock_brave_search.assert_any_call("Main Topic: Testing LLMs Angle 1: Integration", count=3)
    mock_brave_search.assert_any_call("Main Topic: Testing LLMs Angle 2: Quality Challenges", count=3)

    assert mock_anthropic_create.call_count == 2
    # Check that prompts contained search results (simplified check)
    first_anthropic_call_args = mock_anthropic_create.call_args_list[0]
    second_anthropic_call_args = mock_anthropic_create.call_args_list[1]
    assert "Snippet A for angle 1" in first_anthropic_call_args.kwargs['prompt']
    assert "Snippet B for angle 2" in second_anthropic_call_args.kwargs['prompt']
    assert "Angle 1: Integration" in first_anthropic_call_args.kwargs['prompt']
    assert "Angle 2: Quality Challenges" in second_anthropic_call_args.kwargs['prompt']


def test_generate_post_no_angles(client, mocker):
    """Test successful post generation with no specific angles (uses topic for search/angle)."""
    # Simplified mocking, only need one search result and one completion
    mock_style_id = "67f3917fd2cccab061470338"
    mock_style_doc = {"_id": ObjectId(mock_style_id), "name": "Gen Style No Angles", "analysis": {"overall_tone": "Simple"}}
    mock_styles_collection_gen = MagicMock()
    mock_styles_collection_gen.find_one.return_value = mock_style_doc
    mock_db_gen = MagicMock()
    mock_db_gen.styles = mock_styles_collection_gen
    mocker.patch('app.mongo.db', mock_db_gen)

    mock_search_results = [{"title": "Brave Result Topic", "description": "Snippet for main topic"}]
    mock_brave_search = mocker.patch('app.perform_brave_search', return_value=mock_search_results)

    mock_completion = MagicMock()
    mock_completion.completion = "Generated Post Draft for Main Topic."
    mock_anthropic_create = mocker.patch('app.anthropic_client.completions.create', return_value=mock_completion)

    request_data = {
        "style_id": mock_style_id,
        "topic": "Main Topic Only",
        "key_points": "- Point A",
        # No subjects_or_angles
    }
    res = client.post(url_for('generate_post'), json=request_data)

    assert res.status_code == 200
    response_data = res.get_json()
    assert "generated_posts" in response_data
    assert len(response_data["generated_posts"]) == 1
    assert response_data["generated_posts"][0] == "Generated Post Draft for Main Topic."
    mock_brave_search.assert_called_once()
    # Check search query was based on topic using positional arg
    mock_brave_search.assert_called_with("Main Topic Only Main Topic Only", count=3)
    mock_anthropic_create.assert_called_once()
    # Check prompt contained topic search result and topic as angle
    anthropic_call_args = mock_anthropic_create.call_args_list[0]
    prompt_text = anthropic_call_args.kwargs['prompt']
    assert "Snippet for main topic" in prompt_text
    # Corrected assertion to match actual prompt format
    assert f"- **Specific Angle/Focus for this draft:** {request_data['topic']}" in prompt_text
    assert f"Ensure the post focuses on the angle: '{request_data['topic']}'" in prompt_text


# TODO: Add tests for:
# - Analyze style errors (Anthropic/DB)
# - /api/styles (GET)
# - Generate post errors (Style not found, Brave error, Anthropic error)
