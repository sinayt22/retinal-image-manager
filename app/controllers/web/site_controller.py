import logging
from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.services.site_service import SiteService

site_bp = Blueprint('sites', __name__)
site_service = SiteService()

logger = logging.getLogger(__name__)

@site_bp.route('/', methods=['GET'])
def index():
    """List all sites."""
    sites = site_service.get_all_sites()
    return render_template('sites/index.html', sites=sites)

@site_bp.route('/new', methods=['GET'])
def new():
    """Show form to create a new site."""
    return render_template('sites/new.html')

@site_bp.route('/', methods=['POST'])
def create():
    """Create a new site."""
    name = request.form.get('name')
    location = request.form.get('location')
    
    if not name:
        flash('Site name is required', 'error')
        return render_template('sites/new.html'), 400
    
    try:
        # Check if site with this name already exists
        existing_site = site_service.get_site_by_name(name)
        if existing_site:
            flash(f'Site with name "{name}" already exists', 'error')
            return render_template('sites/new.html'), 400
        
        site_data = {'name': name, 'location': location}
        site = site_service.create_site(site_data)
        
        logger.info(f"Site created successfully with id={site.id}")
        flash("Site created successfully!", "success")
        return redirect(url_for('sites.index'))
    except Exception as e:
        logger.error(f"Failed to create site: {str(e)}", exc_info=True)
        flash(f"Error creating site: {str(e)}", "error")
        return render_template('sites/new.html'), 500

@site_bp.route('/<int:id>', methods=['GET'])
def show(id):
    """Show site details."""
    site = site_service.get_site_by_id(id)
    if not site:
        flash(f"Site with id {id} not found", "error")
        return redirect(url_for('sites.index'))
    return render_template('sites/show.html', site=site)

@site_bp.route('/<int:id>/edit', methods=['GET'])
def edit(id):
    """Show form to edit an existing site."""
    site = site_service.get_site_by_id(id)
    if not site:
        flash(f"Site with id {id} not found", "error")
        return redirect(url_for('sites.index'))
    return render_template('sites/edit.html', site=site)

@site_bp.route('/<int:id>', methods=['POST'])
def update(id):
    """Update an existing site."""
    site = site_service.get_site_by_id(id)
    if not site:
        flash(f"Site with id {id} not found", "error")
        return redirect(url_for('sites.index'))
    
    name = request.form.get('name')
    location = request.form.get('location')
    
    if not name:
        flash('Site name is required', 'error')
        return render_template('sites/edit.html', site=site), 400
    
    try:
        # Check if another site with this name already exists
        existing_site = site_service.get_site_by_name(name)
        if existing_site and existing_site.id != id:
            flash(f'Another site with name "{name}" already exists', 'error')
            return render_template('sites/edit.html', site=site), 400
        
        site_data = {'name': name, 'location': location}
        site_service.update_site(id, site_data)
        
        logger.info(f"Site updated successfully with id={id}")
        flash("Site updated successfully!", "success")
        return redirect(url_for('sites.index'))
    except Exception as e:
        logger.error(f"Failed to update site: {str(e)}", exc_info=True)
        flash(f"Error updating site: {str(e)}", "error")
        return render_template('sites/edit.html', site=site), 500

@site_bp.route('/<int:id>/delete', methods=['POST'])
def delete(id):
    """Delete a site."""
    site = site_service.get_site_by_id(id)
    if not site:
        flash(f"Site with id {id} not found", "error")
        return redirect(url_for('sites.index'))
    
    try:
        site_service.delete_site(id)
        logger.info(f"Site deleted successfully with id={id}")
        flash("Site deleted successfully!", "success")
        return redirect(url_for('sites.index'))
    except Exception as e:
        logger.error(f"Failed to delete site: {str(e)}", exc_info=True)
        flash(f"Error deleting site: {str(e)}", "error")
        return redirect(url_for('sites.index'))