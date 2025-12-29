"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities

# Test client for FastAPI
client = TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state before each test"""
    # Store original state
    original_state = {
        name: {
            "description": details["description"],
            "schedule": details["schedule"],
            "max_participants": details["max_participants"],
            "participants": details["participants"].copy()
        }
        for name, details in activities.items()
    }
    
    yield
    
    # Restore original state
    for name, details in original_state.items():
        activities[name]["participants"] = details["participants"].copy()


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_list(self):
        """Test that /activities endpoint returns a dictionary of activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0
    
    def test_get_activities_contains_required_fields(self):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_details in data.items():
            assert "description" in activity_details
            assert "schedule" in activity_details
            assert "max_participants" in activity_details
            assert "participants" in activity_details
            assert isinstance(activity_details["participants"], list)
    
    def test_get_activities_contains_known_activities(self):
        """Test that known activities are present"""
        response = client.get("/activities")
        data = response.json()
        
        expected_activities = [
            "Chess Club",
            "Programming Class",
            "Basketball Team"
        ]
        
        for activity in expected_activities:
            assert activity in data


class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_valid_activity_and_email(self, reset_activities):
        """Test successful signup for a valid activity"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
    
    def test_signup_adds_participant_to_activity(self, reset_activities):
        """Test that signup actually adds the participant to the activity"""
        email = "testuser@mergington.edu"
        response = client.post(
            f"/activities/Tennis%20Club/signup?email={email}"
        )
        assert response.status_code == 200
        
        # Verify participant was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email in activities_data["Tennis Club"]["participants"]
    
    def test_signup_nonexistent_activity(self):
        """Test signup for non-existent activity returns 404"""
        response = client.post(
            "/activities/NonExistent%20Activity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_signup_duplicate_participant(self, reset_activities):
        """Test that duplicate signup is rejected"""
        email = "michael@mergington.edu"  # Already in Chess Club
        response = client.post(
            f"/activities/Chess%20Club/signup?email={email}"
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]
    
    def test_signup_activity_full(self, reset_activities):
        """Test signup for activity that's full"""
        # Tennis Club has max 10 participants and currently has 1
        # Add 9 more to fill it
        for i in range(9):
            client.post(
                f"/activities/Tennis%20Club/signup?email=filler{i}@mergington.edu"
            )
        
        # Try to add one more
        response = client.post(
            "/activities/Tennis%20Club/signup?email=overflow@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "full" in data["detail"].lower()


class TestUnregister:
    """Tests for DELETE /activities/{activity_name}/participants endpoint"""
    
    def test_unregister_existing_participant(self, reset_activities):
        """Test successful unregister of existing participant"""
        email = "michael@mergington.edu"  # Already in Chess Club
        response = client.delete(
            f"/activities/Chess%20Club/participants?email={email}"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Removed" in data["message"]
        assert email in data["message"]
    
    def test_unregister_removes_participant(self, reset_activities):
        """Test that unregister actually removes the participant"""
        email = "michael@mergington.edu"
        
        # Verify participant is in activity before
        activities_response = client.get("/activities")
        assert email in activities_response.json()["Chess Club"]["participants"]
        
        # Unregister
        client.delete(f"/activities/Chess%20Club/participants?email={email}")
        
        # Verify participant is removed
        activities_response = client.get("/activities")
        assert email not in activities_response.json()["Chess Club"]["participants"]
    
    def test_unregister_nonexistent_activity(self):
        """Test unregister from non-existent activity returns 404"""
        response = client.delete(
            "/activities/NonExistent%20Activity/participants?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_unregister_nonexistent_participant(self, reset_activities):
        """Test unregister of non-existent participant returns 404"""
        response = client.delete(
            "/activities/Chess%20Club/participants?email=nonexistent@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Student not found" in data["detail"]


class TestIntegration:
    """Integration tests for signup and unregister flow"""
    
    def test_signup_then_unregister_flow(self, reset_activities):
        """Test complete signup and unregister flow"""
        email = "integration@mergington.edu"
        activity = "Programming%20Class"
        
        # Sign up
        signup_response = client.post(f"/activities/{activity}/signup?email={email}")
        assert signup_response.status_code == 200
        
        # Verify participant is in activity
        activities_response = client.get("/activities")
        assert email in activities_response.json()["Programming Class"]["participants"]
        
        # Unregister
        unregister_response = client.delete(
            f"/activities/{activity}/participants?email={email}"
        )
        assert unregister_response.status_code == 200
        
        # Verify participant is removed
        activities_response = client.get("/activities")
        assert email not in activities_response.json()["Programming Class"]["participants"]
    
    def test_multiple_signups_for_different_activities(self, reset_activities):
        """Test participant can sign up for multiple activities"""
        email = "multisignup@mergington.edu"
        
        # Sign up for multiple activities
        response1 = client.post(f"/activities/Chess%20Club/signup?email={email}")
        response2 = client.post(f"/activities/Gym%20Class/signup?email={email}")
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Verify in both activities
        activities_response = client.get("/activities")
        data = activities_response.json()
        assert email in data["Chess Club"]["participants"]
        assert email in data["Gym Class"]["participants"]


class TestRoot:
    """Tests for root endpoint"""
    
    def test_root_redirects(self):
        """Test that root endpoint redirects to static index"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]
