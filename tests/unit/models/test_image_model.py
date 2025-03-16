import pytest
from datetime import datetime, timezone
from app.models.image import Image, EyeSide, ImageQualityScore, AnatomyScore


class TestImageModel:
    @pytest.fixture
    def sample_image(self):
        """Create a sample image for testing."""
        return Image(
            id=1,
            patient_id=1,
            eye_side=EyeSide.LEFT,
            quality_score=ImageQualityScore.HIGH,
            anatomy_score=AnatomyScore.GOOD,
            site_id=1,
            over_illuminated=False,
            image_path="test_image.jpg",
            acquisition_date=datetime(2025, 3, 1, tzinfo=timezone.utc),
            created_at=datetime(2025, 3, 1, tzinfo=timezone.utc),
            modified_at=datetime(2025, 3, 1, tzinfo=timezone.utc)
        )
    
    def test_image_creation(self, sample_image):
        """Test the creation of an image instance."""
        assert sample_image.id == 1
        assert sample_image.patient_id == 1
        assert sample_image.eye_side == EyeSide.LEFT
        assert sample_image.quality_score == ImageQualityScore.HIGH
        assert sample_image.anatomy_score == AnatomyScore.GOOD
        assert sample_image.site_id == 1
        assert sample_image.over_illuminated is False
        assert sample_image.image_path == "test_image.jpg"
        assert sample_image.acquisition_date.year == 2025
        assert sample_image.acquisition_date.month == 3
        assert sample_image.acquisition_date.day == 1
    
    def test_image_repr(self, sample_image):
        """Test the string representation of an image."""
        assert repr(sample_image) == "<image 1 - EyeSide.LEFT>"
    
    def test_image_to_dict(self, sample_image):
        """Test the to_dict method."""
        image_dict = sample_image.to_dict()
        
        assert image_dict["id"] == 1
        assert image_dict["patient_id"] == 1
        assert image_dict["eye_side"] == "LEFT"
        assert image_dict["quality_score"] == "HIGH"
        assert image_dict["anatomy_score"] == "GOOD"
        assert image_dict["site_id"] == 1
        assert image_dict["over_illumination"] is False
        assert image_dict["image_path"] == "test_image.jpg"
        assert "acquisition_date" in image_dict
        assert "created_at" in image_dict
        assert "updated_at" in image_dict
    
    def test_enum_values(self):
        """Test enum values for the Image model."""
        # Test EyeSide enum
        assert EyeSide.LEFT.value == "LEFT"
        assert EyeSide.RIGHT.value == "RIGHT"
        
        # Test ImageQualityScore enum
        assert ImageQualityScore.LOW.value == "LOW"
        assert ImageQualityScore.ACCEPTABLE.value == "ACCEPTABLE"
        assert ImageQualityScore.HIGH.value == "HIGH"
        
        # Test AnatomyScore enum
        assert AnatomyScore.POOR.value == "POOR"
        assert AnatomyScore.ACCEPTABLE.value == "ACCEPTABLE"
        assert AnatomyScore.GOOD.value == "GOOD"