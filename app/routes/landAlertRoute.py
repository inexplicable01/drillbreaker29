"""
Land/Infill Property Alert Routes

Flask blueprint providing JSON API endpoints and HTML admin interface
for managing land/infill property candidates.
"""

from flask import Blueprint, request, jsonify, render_template
from app.DBModels.LandAlertCandidate import landalertcandidatecontroller
from app.LandAlertSelector import land_alert_selector
from app.DBFunc.BriefListingController import brieflistingcontroller
from app.config import land_alert_config as config

land_alert_bp = Blueprint('land_alerts', __name__, url_prefix='/land_alerts')


# =============================================================================
# JSON API ENDPOINTS
# =============================================================================

@land_alert_bp.route('/api/candidates', methods=['GET'])
def get_candidates():
    """
    Get all land alert candidates with optional filtering.

    Query Parameters:
        status: Filter by status (new, reviewed, interested, rejected, contacted)
        min_score: Minimum score threshold
        limit: Max number of results

    Returns:
        JSON array of candidate objects
    """
    status = request.args.get('status')
    min_score = request.args.get('min_score', type=int)
    limit = request.args.get('limit', type=int)

    candidates = landalertcandidatecontroller.get_all(status=status, min_score=min_score)

    if limit:
        candidates = candidates[:limit]

    return jsonify([c.to_dict() for c in candidates]), 200


@land_alert_bp.route('/api/candidates/<int:candidate_id>', methods=['GET'])
def get_candidate(candidate_id):
    """Get a single candidate by ID."""
    candidate = landalertcandidatecontroller.get_by_id(candidate_id)

    if not candidate:
        return jsonify({'error': 'Candidate not found'}), 404

    return jsonify(candidate.to_dict()), 200


@land_alert_bp.route('/api/candidates/<int:candidate_id>/status', methods=['PUT'])
def update_candidate_status(candidate_id):
    """
    Update candidate status and add admin notes.

    Request Body (JSON):
        {
            "status": "reviewed|interested|rejected|contacted",
            "admin_notes": "Optional notes"
        }
    """
    data = request.get_json()

    if not data or 'status' not in data:
        return jsonify({'error': 'Status is required'}), 400

    new_status = data['status']
    admin_notes = data.get('admin_notes')

    # Validate status
    valid_statuses = ['new', 'reviewed', 'interested', 'rejected', 'contacted']
    if new_status not in valid_statuses:
        return jsonify({'error': f'Invalid status. Must be one of: {valid_statuses}'}), 400

    candidate = landalertcandidatecontroller.update_status(
        candidate_id, new_status, admin_notes
    )

    if not candidate:
        return jsonify({'error': 'Candidate not found'}), 404

    return jsonify(candidate.to_dict()), 200


@land_alert_bp.route('/api/candidates/<int:candidate_id>', methods=['DELETE'])
def delete_candidate(candidate_id):
    """Delete a candidate."""
    success = landalertcandidatecontroller.delete(candidate_id)

    if not success:
        return jsonify({'error': 'Candidate not found'}), 404

    return jsonify({'message': 'Candidate deleted successfully'}), 200


@land_alert_bp.route('/api/stats', methods=['GET'])
def get_stats():
    """
    Get candidate statistics.

    Returns:
        JSON object with status counts and top candidates
    """
    status_counts = landalertcandidatecontroller.count_by_status()
    top_candidates = landalertcandidatecontroller.get_top_candidates(limit=10, status='new')

    return jsonify({
        'status_counts': status_counts,
        'top_candidates': [c.to_dict() for c in top_candidates],
        'config': {
            'min_lot_size': config.MIN_LOT_SIZE_SQFT,
            'price_range': {'min': config.MIN_PRICE, 'max': config.MAX_PRICE},
            'min_score_threshold': config.MIN_SCORE_THRESHOLD,
            'target_cities': config.TARGET_CITIES
        }
    }), 200


@land_alert_bp.route('/api/scan', methods=['POST'])
def trigger_scan():
    """
    Manually trigger a property scan.

    Request Body (JSON):
        {
            "limit": 100,           // Optional: limit listings to scan
            "min_score": 50         // Optional: override min score
        }

    Returns:
        Scan statistics
    """
    data = request.get_json() or {}
    limit = data.get('limit')
    min_score = data.get('min_score')

    stats = land_alert_selector.scan_and_score_listings(
        limit=limit,
        min_score=min_score
    )

    return jsonify(stats), 200


@land_alert_bp.route('/api/score/<int:zpid>', methods=['GET'])
def score_single_property(zpid):
    """
    Score a single property by zpid.

    Returns:
        Scoring results for the property
    """
    result = land_alert_selector.score_single_listing(zpid)

    if not result:
        return jsonify({'error': 'Listing not found'}), 404

    return jsonify(result), 200


# =============================================================================
# HTML ADMIN INTERFACE
# =============================================================================

@land_alert_bp.route('/admin', methods=['GET'])
def admin_dashboard():
    """
    Render HTML admin dashboard for managing candidates.
    """
    # Get filter parameters
    status_filter = request.args.get('status', 'new')
    min_score_filter = request.args.get('min_score', type=int, default=config.MIN_SCORE_THRESHOLD)

    # Get candidates
    candidates = landalertcandidatecontroller.get_all(
        status=status_filter if status_filter != 'all' else None,
        min_score=min_score_filter
    )

    # Get stats
    status_counts = landalertcandidatecontroller.count_by_status()

    return render_template(
        'land_alerts/admin_dashboard.html',
        candidates=candidates,
        status_counts=status_counts,
        current_filter=status_filter,
        min_score_filter=min_score_filter,
        config=config
    )


@land_alert_bp.route('/admin/candidate/<int:candidate_id>', methods=['GET'])
def admin_candidate_detail(candidate_id):
    """
    Render detailed view of a single candidate.
    """
    candidate = landalertcandidatecontroller.get_by_id(candidate_id)

    if not candidate:
        return "Candidate not found", 404

    # Get associated BriefListing for full details
    listing = brieflistingcontroller.getListingByzpid(candidate.zpid)

    return render_template(
        'land_alerts/candidate_detail.html',
        candidate=candidate,
        listing=listing
    )