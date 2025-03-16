import pytest
from datetime import datetime, timezone
from app.models.site import Site


class TestSiteModel:
    @pytest.fixture
    def sample_site(self):
        """Create a sample site for testing."""
        return Site(
            id=1,
            name="Main Clinic",
            location="New York, NY",
            created_at=datetime(2025, 3, 1, tzinfo=timezone.utc),
            modified_at=datetime(2025, 3, 1, tzinfo=timezone.utc)
        )
    
    def test_site_creation(self, sample_site):
        """Test the creation of a site instance."""
        assert sample_site.id == 1
        assert sample_site.name == "Main Clinic"
        assert sample_site.location == "New York, NY"
        assert sample_site.created_at.year == 2025
        assert sample_site.created_at.month == 3
        assert sample_site.created_at.day == 1
    
    def test_site_repr(self, sample_site):
        """Test the string representation of a site."""
        assert repr(sample_site) == "<Site 1: Main Clinic>"
    
    def test_site_to_dict(self, sample_site):
        """Test the to_dict method."""
        site_dict = sample_site.to_dict()
        
        assert site_dict["id"] == 1
        assert site_dict["name"] == "Main Clinic"
        assert site_dict["location"] == "New York, NY"
        assert "created_at" in site_dict
        assert "modified_at" in site_dict