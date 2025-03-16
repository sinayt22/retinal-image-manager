import pytest
from app.models.site import Site
from app.services.site_service import SiteService


@pytest.mark.usefixtures('app_context')
class TestSiteService:
    @pytest.fixture
    def site_service(self):
        return SiteService()
    
    @pytest.fixture
    def db_session(self, monkeypatch):
        """
        Create a mock db session with methods that can be monitored
        """
        class MockSession:
            def __init__(self):
                self.added = []
                self.deleted = []
                self.committed = False
            
            def add(self, obj):
                self.added.append(obj)
            
            def delete(self, obj):
                self.deleted.append(obj)
            
            def commit(self):
                self.committed = True
                
            def remove(self):
                pass  # Required for teardown_appcontext
        
        mock_session = MockSession()
        
        # Patch the db.session in the app
        monkeypatch.setattr('app.services.site_service.db.session', mock_session)
        
        return mock_session
    
    def test_get_all_sites(self, site_service, monkeypatch):
        # Mock data
        mock_sites = [
            Site(id=1, name="Main Clinic"),
            Site(id=2, name="Branch Office")
        ]
        
        # Mock the query
        class MockQuery:
            def order_by(self, _):
                return self
                
            def all(self):
                return mock_sites
        
        monkeypatch.setattr(Site, 'query', MockQuery())
        
        # Test
        sites = site_service.get_all_sites()
        
        # Assertions
        assert len(sites) == 2
        assert sites[0].id == 1
        assert sites[1].id == 2
    
    def test_get_site_by_id(self, site_service, monkeypatch):
        # Mock data
        mock_site = Site(id=1, name="Main Clinic", location="New York, NY")
        
        # Mock the query
        class MockQuery:
            def get(self, id):
                if id == 1:
                    return mock_site
                return None
        
        monkeypatch.setattr(Site, 'query', MockQuery())
        
        # Test
        site = site_service.get_site_by_id(1)
        
        # Assertions
        assert site is not None
        assert site.id == 1
        assert site.name == "Main Clinic"
        assert site.location == "New York, NY"
        
        # Test non-existent site
        site = site_service.get_site_by_id(999)
        assert site is None
    
    def test_get_site_by_name(self, site_service, monkeypatch):
        # Mock data
        mock_site = Site(id=1, name="Main Clinic", location="New York, NY")
        
        # Mock the query
        class MockQuery:
            def filter_by(self, **kwargs):
                return self
                
            def first(self):
                return mock_site
        
        monkeypatch.setattr(Site, 'query', MockQuery())
        
        # Test
        site = site_service.get_site_by_name("Main Clinic")
        
        # Assertions
        assert site is not None
        assert site.id == 1
        assert site.name == "Main Clinic"
    
    def test_create_site(self, site_service, db_session, monkeypatch):
        # Mock data
        site_data = {
            'name': 'New Clinic',
            'location': 'Chicago, IL'
        }
        
        # Instead of mocking __init__, mock the entire Site class
        class MockSite:
            def __init__(self, **kwargs):
                self.id = 1
                self.name = kwargs.get('name')
                self.location = kwargs.get('location')
        
        # Replace the Site class in the service
        monkeypatch.setattr('app.services.site_service.Site', MockSite)
        
        # Test
        site = site_service.create_site(site_data)
        
        # Assertions
        assert site is not None
        assert site.id == 1
        assert site.name == 'New Clinic'
        assert site.location == 'Chicago, IL'
        
        # Check if session methods were called
        assert len(db_session.added) == 1
        assert db_session.committed is True
    
    def test_update_site(self, site_service, db_session, monkeypatch):
        # Mock data
        mock_site = Site(id=1, name="Main Clinic", location="New York, NY")
        
        # Mock the get_site_by_id method
        monkeypatch.setattr(
            site_service, 
            'get_site_by_id', 
            lambda id: mock_site if id == 1 else None
        )
        
        # Update data
        update_data = {
            'name': 'Updated Clinic',
            'location': 'Updated Location'
        }
        
        # Test
        updated_site = site_service.update_site(1, update_data)
        
        # Assertions
        assert updated_site is not None
        assert updated_site.name == 'Updated Clinic'
        assert updated_site.location == 'Updated Location'
        assert db_session.committed is True
        
        # Test updating non-existent site
        with pytest.raises(ValueError, match="Site with ID 999 not found"):
            site_service.update_site(999, update_data)
    
    def test_delete_site(self, site_service, db_session, monkeypatch):
        # Mock data
        mock_site = Site(id=1, name="Main Clinic", location="New York, NY")
        
        # Mock the get_site_by_id method
        monkeypatch.setattr(
            site_service, 
            'get_site_by_id', 
            lambda id: mock_site if id == 1 else None
        )
        
        # Test
        result = site_service.delete_site(1)
        
        # Assertions
        assert result is True
        assert len(db_session.deleted) == 1
        assert db_session.committed is True
        
        # Test deleting non-existent site
        with pytest.raises(ValueError, match="Site with ID 999 not found"):
            site_service.delete_site(999)
    
    def test_find_or_create_site(self, site_service, monkeypatch):
        # First scenario: site exists
        existing_site = Site(id=1, name="Existing Clinic")
        
        # Mock the get_site_by_name method for first test
        monkeypatch.setattr(
            site_service,
            'get_site_by_name',
            lambda name: existing_site if name == "Existing Clinic" else None
        )
        
        # Test finding existing site
        site = site_service.find_or_create_site("Existing Clinic")
        assert site is existing_site
        
        # Second scenario: site doesn't exist
        new_site = Site(id=2, name="New Clinic")
        
        # Mock methods for second test
        monkeypatch.setattr(
            site_service,
            'get_site_by_name',
            lambda name: None  # Return None for any name (site doesn't exist)
        )
        monkeypatch.setattr(
            site_service,
            'create_site',
            lambda data: new_site
        )
        
        # Test creating new site
        site = site_service.find_or_create_site("New Clinic")
        assert site is new_site