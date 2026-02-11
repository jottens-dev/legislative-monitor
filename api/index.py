from flask import Flask, jsonify, request
from datetime import datetime
import json
import os
import sys

# Add parent directory to path so we can import our scraper
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from multi_government_scraper import MultiGovernmentMonitor

app = Flask(__name__)
monitor = MultiGovernmentMonitor()

# For Vercel serverless functions, we can't easily persist state to disk
# The shortcut will handle comparing dates
# Or we could add Vercel KV later for state storage

@app.route('/api/check', methods=['GET'])
@app.route('/check', methods=['GET'])
def check_updates():
    """Check for new legislative updates across all three levels"""
    # For Vercel, we always check latest (no state persistence in this version)
    # The iPhone shortcut can handle date comparisons
    results = monitor.check_all(last_check_date=None)
    
    # Check if any government has new content
    has_any_new = any(
        gov['has_new_content'] 
        for gov in results['governments']
    )
    
    if has_any_new:
        response = {
            'status': 'new_content',
            'checked_at': datetime.now().isoformat(),
            'governments': results['governments'],
            'summary': {
                'factual': generate_factual_summary(results),
                'neutral_analysis': generate_neutral_analysis(results),
                'strategic_analysis': generate_strategic_analysis(results)
            }
        }
    else:
        response = {
            'status': 'no_new_content',
            'checked_at': datetime.now().isoformat(),
            'message': 'No new legislative activity found.'
        }
    
    return jsonify(response)

@app.route('/api/latest', methods=['GET'])
@app.route('/latest', methods=['GET'])
def get_latest():
    """Get the latest info from all levels"""
    results = monitor.check_all()
    
    return jsonify({
        'status': 'success',
        'governments': results['governments'],
        'summary': generate_factual_summary(results)
    })

@app.route('/health', methods=['GET'])
@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy', 
        'service': 'multi-government-legislative-api',
        'platform': 'vercel',
        'monitoring': [
            'Alberta Legislature',
            'House of Commons (Canada)',
            'Strathcona County Council'
        ]
    })

@app.route('/', methods=['GET'])
def home():
    """Root endpoint"""
    return jsonify({
        'message': 'Legislative Monitor API',
        'endpoints': {
            'check': '/api/check - Check for new updates',
            'latest': '/api/latest - Get latest info',
            'health': '/health - Health check'
        }
    })

def generate_factual_summary(results):
    """Generate a dry, factual summary across all levels"""
    summary_lines = []
    
    # Alberta
    alberta = results['governments'][0]
    if alberta['has_new_content']:
        summary_lines.append("ALBERTA LEGISLATURE:")
        for item in alberta['new_items']:
            summary_lines.append(f"  • {item['full_text']}")
        summary_lines.append("")
    
    # Canada
    canada = results['governments'][1]
    if canada['has_new_content']:
        summary_lines.append("HOUSE OF COMMONS (CANADA):")
        for item in canada['new_items']:
            summary_lines.append(f"  • {item['full_text']}")
        summary_lines.append("")
    
    # Strathcona County
    strathcona = results['governments'][2]
    if strathcona['has_new_content']:
        summary_lines.append("STRATHCONA COUNTY COUNCIL:")
        for item in strathcona['new_items']:
            summary_lines.append(f"  • {item['full_text']}")
        summary_lines.append("")
    
    if not summary_lines:
        return "No new legislative activity."
    
    summary_lines.append("[Full details require document parsing]")
    return "\n".join(summary_lines)

def generate_neutral_analysis(results):
    """Generate neutral political analysis"""
    active_levels = [
        gov['name'] for gov in results['governments'] 
        if gov['has_new_content']
    ]
    
    if not active_levels:
        return ""
    
    levels_str = ", ".join(active_levels)
    return (f"Legislative activity occurred at: {levels_str}. "
            "Detailed policy analysis requires content extraction from documents.")

def generate_strategic_analysis(results):
    """Generate analysis of political strategy and implications"""
    active_levels = [
        gov['name'] for gov in results['governments'] 
        if gov['has_new_content']
    ]
    
    if not active_levels:
        return ""
    
    return ("Strategic implications and inter-governmental dynamics require "
            "detailed document analysis. Check full transcripts for context.")

# This is what Vercel calls
app = app
