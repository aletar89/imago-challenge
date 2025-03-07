from app.services.media_fetch_service import MediaFetchService
from app.models.media_item import MediaItem


def test_normalize_media_item():
    """Test the normalize_media_item static method."""
    # Create a test MediaItem with HTML content
    media_item = MediaItem(
        id="test123",
        title="Test <script>alert('XSS')</script> Title",
        description="<p>Test Description with <b>HTML</b></p>",
        photographer="Test <iframe>Photographer</iframe>",
        date="2020-01-01",
        thumbnail_url="https://example.com/image.jpg",
        additional_data={
            "script": "<script>alert('XSS')</script>",
        },
    )

    # Normalize the media item
    MediaFetchService.normalize_media_item(media_item)

    assert media_item.title == "Test alert('XSS') Title"
    assert media_item.photographer == "Test Photographer"
    assert media_item.description == "Test Description with HTML"
    assert media_item.additional_data["script"] == "alert('XSS')"
