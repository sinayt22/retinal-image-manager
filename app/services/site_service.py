from app.models.site import Site
from app import db

class SiteService:

    def get_all_sites(self):
        return Site.query.order_by(Site.name).all()
    
    def get_site_by_id(self,site_id):
        return Site.query.get(site_id)
    
    def get_site_by_name(self, site_name):
        return Site.query.filter_by(name=site_name).first()
    
    def create_site(self, site_data):
        site = Site(
            name=site_data.get('name'),
            location=site_data.get('location')
        )

        db.session.add(site)
        db.session.commit()
        return site
    
    def update_site(self, site_id, site_data):
        site = self.get_site_by_id(site_id)
        
        if not site:
            raise ValueError(f"Site with ID {site_id} not found")
        
        if 'name' in site_data:
            site.name = site_data['name']
        if 'location' in site_data:
            site.location = site_data['location']
        
        db.session.commit()
        return site
    
    def delete_site(self, site_id):
        site = self.get_site_by_id(site_id)

        if not site:
            raise ValueError(f"Site with ID {site_id} not found")

        db.session.delete(site)
        db.session.commit()
        return True

    def find_or_create_site(self, name, location=None):
        site = self.get_site_by_name(name)
        if not site:
            site = self.create_site({'name':name, 'location': location})

        return site 

    