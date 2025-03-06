"""Main routes for the application.

This module defines the main routes for rendering the HTML frontend.
"""

from flask import Blueprint, render_template

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    """Render the main page"""
    return render_template("index.html")
