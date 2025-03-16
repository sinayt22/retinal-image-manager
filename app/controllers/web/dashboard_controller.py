import logging
from flask import Blueprint, render_template, jsonify

from app.services.statistics_service import StatisticsService

dashboard_bp = Blueprint('dashboard', __name__)
statistics_service = StatisticsService()

logger = logging.getLogger(__name__)

@dashboard_bp.route('/', methods=['GET'])
def index():
    """Display the main dashboard."""
    site_stats = statistics_service.get_sites_statistics()
    image_stats = statistics_service.get_image_quality_statistics()
    
    return render_template(
        'dashboard/index.html', 
        site_stats=site_stats,
        image_stats=image_stats
    )

@dashboard_bp.route('/api/site-statistics', methods=['GET'])
def site_statistics_api():
    """API endpoint for retrieving site statistics data for charts."""
    try:
        site_stats = statistics_service.get_sites_statistics()
        return jsonify({
            'status': 'success',
            'data': site_stats
        })
    except Exception as e:
        logger.error(f"Error retrieving site statistics: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f"Failed to retrieve statistics: {str(e)}"
        }), 500

@dashboard_bp.route('/api/image-statistics', methods=['GET'])
def image_statistics_api():
    """API endpoint for retrieving image quality statistics data for charts."""
    try:
        image_stats = statistics_service.get_image_quality_statistics()
        return jsonify({
            'status': 'success',
            'data': image_stats
        })
    except Exception as e:
        logger.error(f"Error retrieving image statistics: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f"Failed to retrieve statistics: {str(e)}"
        }), 500