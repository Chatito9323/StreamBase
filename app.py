import os
import json
import uuid
import logging
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configuration
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'svg'}
ADMIN_EMAIL = "admin@access.com"

# Initialize Supabase client
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_ANON_KEY")

if not supabase_url or not supabase_key:
    logging.error("Supabase credentials not found in environment variables")
    supabase = None
else:
    try:
        supabase: Client = create_client(supabase_url, supabase_key)
        logging.info("Supabase client initialized successfully")
    except Exception as e:
        logging.error(f"Failed to initialize Supabase client: {e}")
        supabase = None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_services():
    """Load services from Supabase"""
    if not supabase:
        logging.error("Supabase client not available")
        return []
    
    try:
        response = supabase.table('services').select('*').order('created_at', desc=False).execute()
        return response.data or []
    except Exception as e:
        logging.error(f"Error loading services from Supabase: {e}")
        return []

def save_service(service_data):
    """Save service to Supabase"""
    if not supabase:
        logging.error("Supabase client not available")
        return False
    
    try:
        service_id = service_data.get('id')
        
        # Remove id from data for insert/update
        data_to_save = {k: v for k, v in service_data.items() if k != 'id'}
        data_to_save['updated_at'] = datetime.utcnow().isoformat()
        
        if service_id:
            # Update existing service
            response = supabase.table('services').update(data_to_save).eq('id', service_id).execute()
        else:
            # Create new service
            data_to_save['created_at'] = datetime.utcnow().isoformat()
            data_to_save['has_new_accounts'] = True  # Mark as having new accounts
            response = supabase.table('services').insert(data_to_save).execute()
        
        logging.info("Service saved successfully")
        return True
    except Exception as e:
        logging.error(f"Error saving service to Supabase: {e}")
        return False

def delete_service(service_id):
    """Delete service from Supabase"""
    if not supabase:
        logging.error("Supabase client not available")
        return False
    
    try:
        response = supabase.table('services').delete().eq('id', service_id).execute()
        logging.info(f"Service {service_id} deleted successfully")
        return True
    except Exception as e:
        logging.error(f"Error deleting service from Supabase: {e}")
        return False

def upload_icon_to_supabase(file):
    """Upload icon to Supabase Storage"""
    if not supabase:
        logging.error("Supabase client not available")
        return None
    
    try:
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        
        # Read file content
        file.seek(0)  # Reset file pointer
        file_content = file.read()
        
        # Try to create bucket first if it doesn't exist
        try:
            supabase.storage.create_bucket('service-icons')
            logging.info("Created service-icons bucket")
        except Exception as bucket_error:
            logging.info(f"Bucket might already exist: {bucket_error}")
        
        # Upload file to Supabase Storage
        try:
            response = supabase.storage.from_('service-icons').upload(
                unique_filename, 
                file_content,
                file_options={"content-type": file.content_type, "upsert": True}
            )
            
            if response:
                # Get public URL
                public_url = supabase.storage.from_('service-icons').get_public_url(unique_filename)
                logging.info(f"Icon uploaded successfully: {public_url}")
                return public_url
        except Exception as upload_error:
            logging.error(f"Upload failed: {upload_error}")
            # Try alternative upload method
            try:
                response = supabase.storage.from_('service-icons').upload(unique_filename, file_content)
                if response:
                    public_url = supabase.storage.from_('service-icons').get_public_url(unique_filename)
                    logging.info(f"Icon uploaded with alternative method: {public_url}")
                    return public_url
            except Exception as alt_error:
                logging.error(f"Alternative upload also failed: {alt_error}")
        
        return None
    except Exception as e:
        logging.error(f"Error uploading icon to Supabase: {e}")
        return None

def load_service_settings(service_id):
    """Load settings for a specific service from Supabase"""
    default_settings = {
        'placeholders': {
            'user': 'User',
            'pass': 'Pass',
            'expiry': 'Expiry',
            'additional': 'Additional'
        }
    }
    
    if not supabase:
        return default_settings
    
    try:
        response = supabase.table('service_settings').select('*').eq('service_id', service_id).execute()
        if response.data:
            return response.data[0].get('settings', default_settings)
        else:
            return default_settings
    except Exception as e:
        logging.error(f"Error loading service settings from Supabase: {e}")
        return default_settings

def save_service_settings(service_id, settings):
    """Save settings for a specific service to Supabase"""
    if not supabase:
        return False
    
    try:
        # Check if settings exist for this service
        response = supabase.table('service_settings').select('*').eq('service_id', service_id).execute()
        
        if response.data:
            # Update existing settings
            response = supabase.table('service_settings').update({
                'settings': settings,
                'updated_at': datetime.utcnow().isoformat()
            }).eq('service_id', service_id).execute()
        else:
            # Create new settings
            response = supabase.table('service_settings').insert({
                'service_id': service_id,
                'settings': settings,
                'created_at': datetime.utcnow().isoformat()
            }).execute()
        
        return True
    except Exception as e:
        logging.error(f"Error saving service settings to Supabase: {e}")
        return False

def load_settings():
    """Load global settings from Supabase (for backward compatibility)"""
    default_settings = {
        'placeholders': {
            'user': 'User',
            'pass': 'Pass',
            'expiry': 'Expiry',
            'additional': 'Additional'
        }
    }
    
    if not supabase:
        return default_settings
    
    try:
        response = supabase.table('settings').select('*').eq('key', 'global').execute()
        if response.data:
            return response.data[0].get('value', default_settings)
        else:
            return default_settings
    except Exception as e:
        logging.error(f"Error loading settings from Supabase: {e}")
        return default_settings

def save_settings(settings):
    """Save global settings to Supabase (for backward compatibility)"""
    if not supabase:
        return False
    
    try:
        response = supabase.table('settings').update({
            'value': settings,
            'updated_at': datetime.utcnow().isoformat()
        }).eq('key', 'global').execute()
        
        return True
    except Exception as e:
        logging.error(f"Error saving settings to Supabase: {e}")
        return False

def mark_accounts_as_viewed(service_id):
    """Mark service accounts as viewed (remove 'New Accounts!' tag)"""
    if not supabase:
        return False
    
    try:
        response = supabase.table('services').update({
            'has_new_accounts': False,
            'updated_at': datetime.utcnow().isoformat()
        }).eq('id', service_id).execute()
        return True
    except Exception as e:
        logging.error(f"Error updating service viewed status: {e}")
        return False

@app.route('/')
def index():
    services = load_services()
    return render_template('index.html', services=services)

@app.route('/service/<int:service_id>')
def service_detail(service_id):
    services = load_services()
    service = next((s for s in services if s['id'] == service_id), None)
    if not service:
        flash('Service not found', 'error')
        return redirect(url_for('index'))
    
    # Mark accounts as viewed
    mark_accounts_as_viewed(service_id)
    
    # Load service-specific settings
    settings = load_service_settings(service_id)
    placeholders = settings.get('placeholders', {}) if isinstance(settings, dict) else {}
    return render_template('service.html', service=service, placeholders=placeholders)

@app.route('/admin')
def admin_login():
    if session.get('admin_logged_in'):
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_login.html')

@app.route('/admin/login', methods=['POST'])
def admin_login_post():
    email = request.form.get('email', '').strip().lower()
    if email == ADMIN_EMAIL.lower():
        session['admin_logged_in'] = True
        flash('Successfully logged in as admin', 'success')
        return redirect(url_for('admin_dashboard'))
    else:
        flash('Invalid email address', 'error')
        return redirect(url_for('admin_login'))

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    services = load_services()
    return render_template('admin_dashboard.html', services=services)

@app.route('/admin/service/new')
def admin_service_new():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    settings = load_settings()
    placeholders = settings.get('placeholders', {}) if isinstance(settings, dict) else {}
    return render_template('admin_service_form.html', service=None, placeholders=placeholders)

@app.route('/admin/service/<int:service_id>/edit')
def admin_service_edit(service_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    services = load_services()
    service = next((s for s in services if s['id'] == service_id), None)
    if not service:
        flash('Service not found', 'error')
        return redirect(url_for('admin_dashboard'))
    
    # Load service-specific settings
    settings = load_service_settings(service_id)
    placeholders = settings.get('placeholders', {}) if isinstance(settings, dict) else {}
    return render_template('admin_service_form.html', service=service, placeholders=placeholders)

@app.route('/admin/service/save', methods=['POST'])
def admin_service_save():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    service_id = request.form.get('service_id')
    
    # Handle icon upload
    icon_url = None
    if 'icon_file' in request.files:
        file = request.files['icon_file']
        if file and file.filename and allowed_file(file.filename):
            icon_url = upload_icon_to_supabase(file)
            if icon_url:
                logging.info(f"Icon uploaded successfully: {icon_url}")
            else:
                flash('Failed to upload icon', 'error')
    
    # Parse accounts based on account type
    account_type = request.form.get('account_type', 'credentials')
    accounts_text = request.form.get('accounts', '').strip()
    accounts = []
    
    if accounts_text:
        for line in accounts_text.split('\n'):
            line = line.strip()
            if line:
                if account_type == 'cookies':
                    accounts.append({'type': 'cookies', 'data': line})
                else:
                    # Parse credentials format
                    account = {'type': 'credentials'}
                    
                    # Check if it's email:pass format
                    if ':' in line and '|' not in line:
                        parts = line.split(':', 1)
                        if len(parts) == 2:
                            account['user'] = parts[0].strip()
                            account['pass'] = parts[1].strip()
                    else:
                        # Parse pipe-separated format: user|pass|expiry|additional
                        parts = line.split('|')
                        if len(parts) >= 1 and parts[0].strip():
                            account['user'] = parts[0].strip()
                        if len(parts) >= 2 and parts[1].strip():
                            account['pass'] = parts[1].strip()
                        if len(parts) >= 3 and parts[2].strip():
                            account['expiry'] = parts[2].strip()
                        if len(parts) >= 4 and parts[3].strip():
                            account['additional'] = parts[3].strip()
                    
                    accounts.append(account)
    
    service_data = {
        'name': request.form.get('name', '').strip(),
        'icon_class': request.form.get('icon_class', '').strip(),
        'color': request.form.get('color', '').strip(),
        'account_type': account_type,
        'accounts': accounts,
        'comments': request.form.get('comments', '').strip()
    }
    
    # Only update icon_url if a new icon was uploaded
    if icon_url:
        service_data['icon_url'] = icon_url
    
    if service_id:
        service_data['id'] = int(service_id)
    
    if save_service(service_data):
        flash('Service saved successfully', 'success')
    else:
        flash('Error saving service', 'error')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/service/<int:service_id>/delete', methods=['POST'])
def admin_service_delete(service_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    if delete_service(service_id):
        flash('Service deleted successfully', 'success')
    else:
        flash('Error deleting service', 'error')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/settings')
def admin_settings():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    settings = load_settings()
    return render_template('admin_settings.html', settings=settings)

@app.route('/admin/settings/save', methods=['POST'])
def admin_settings_save():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    settings = {
        'placeholders': {
            'user': request.form.get('placeholder_user', 'User').strip(),
            'pass': request.form.get('placeholder_pass', 'Pass').strip(),
            'expiry': request.form.get('placeholder_expiry', 'Expiry').strip(),
            'additional': request.form.get('placeholder_additional', 'Additional').strip()
        }
    }
    
    if save_settings(settings):
        flash('Settings saved successfully', 'success')
    else:
        flash('Error saving settings', 'error')
    
    return redirect(url_for('admin_settings'))

@app.route('/admin/service/<int:service_id>/settings')
def admin_service_settings(service_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    services = load_services()
    service = next((s for s in services if s['id'] == service_id), None)
    if not service:
        flash('Service not found', 'error')
        return redirect(url_for('admin_dashboard'))
    
    settings = load_service_settings(service_id)
    return render_template('admin_service_settings.html', service=service, settings=settings)

@app.route('/admin/service/<int:service_id>/settings/save', methods=['POST'])
def admin_service_settings_save(service_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    settings = {
        'placeholders': {
            'user': request.form.get('placeholder_user', 'User').strip(),
            'pass': request.form.get('placeholder_pass', 'Pass').strip(),
            'expiry': request.form.get('placeholder_expiry', 'Expiry').strip(),
            'additional': request.form.get('placeholder_additional', 'Additional').strip()
        }
    }
    
    if save_service_settings(service_id, settings):
        flash('Service settings saved successfully', 'success')
    else:
        flash('Error saving service settings', 'error')
    
    return redirect(url_for('admin_service_settings', service_id=service_id))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
