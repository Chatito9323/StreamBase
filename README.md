# StreamBase - OTT Accounts & Cookies Manager

A modern web application for managing and distributing OTT (Over-The-Top) streaming service accounts and cookies. Built with Flask and Supabase for scalable account management.

![Python](https://img.shields.io/badge/python-v3.8+-blue.svg)
![Flask](https://img.shields.io/badge/flask-v2.0+-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## Features

- 🎬 **Service Management**: Add and manage multiple OTT streaming services
- 🔐 **Account Distribution**: Support for both credential-based accounts and cookie data
- 🎨 **Custom Branding**: Upload custom icons and set colors for each service
- 📱 **Responsive Design**: Mobile-friendly interface with dark/light theme support
- 👨‍💼 **Admin Dashboard**: Comprehensive admin panel for service management
- ⚙️ **Per-Service Settings**: Customize field labels for each service individually
- 🔔 **New Account Notifications**: Visual indicators for newly added accounts
- 📊 **Account Analytics**: Track account counts and types per service

## Tech Stack

- **Backend**: Flask (Python)
- **Database**: Supabase (PostgreSQL)
- **Storage**: Supabase Storage for icon uploads
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Styling**: Custom CSS with CSS Variables for theming

## Prerequisites

- Python 3.8 or higher
- Supabase account and project
- Modern web browser

## Credits
-- All credit goes to Replit and ChatGPT😅

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/walterwhite-69/StreamBase.git
   cd streambase
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Configuration**
   - Copy `.env.template` to `.env`
   - Update the environment variables with your Supabase credentials:
   ```bash
   cp .env.template .env
   ```

4. **Database Setup**
   
   Create the following tables in your Supabase database:

   **Services Table:**
   ```sql
   CREATE TABLE services (
     id BIGSERIAL PRIMARY KEY,
     name TEXT NOT NULL,
     comments TEXT,
     account_type TEXT DEFAULT 'credentials',
     icon_class TEXT,
     icon_url TEXT,
     color TEXT,
     accounts JSONB DEFAULT '[]',
     has_new_accounts BOOLEAN DEFAULT false,
     created_at TIMESTAMPTZ DEFAULT NOW(),
     updated_at TIMESTAMPTZ DEFAULT NOW()
   );
   ```

   **Service Settings Table:**
   ```sql
   CREATE TABLE service_settings (
     id BIGSERIAL PRIMARY KEY,
     service_id BIGINT REFERENCES services(id) ON DELETE CASCADE,
     settings JSONB DEFAULT '{}',
     created_at TIMESTAMPTZ DEFAULT NOW(),
     updated_at TIMESTAMPTZ DEFAULT NOW()
   );
   ```

   **Global Settings Table:**
   ```sql
   CREATE TABLE settings (
     id BIGSERIAL PRIMARY KEY,
     key TEXT UNIQUE NOT NULL,
     value JSONB DEFAULT '{}',
     created_at TIMESTAMPTZ DEFAULT NOW(),
     updated_at TIMESTAMPTZ DEFAULT NOW()
   );

   INSERT INTO settings (key, value) VALUES (
     'global',
     '{"placeholders": {"user": "User", "pass": "Pass", "expiry": "Expiry", "additional": "Additional"}}'
   );
   ```

   **Storage Bucket:**
   - Create a storage bucket named `service-icons` in your Supabase project
   - Set the bucket to public access for icon display

## Usage

1. **Start the application**
   ```bash
   python app.py
   ```

2. **Access the application**
   - Public interface: `http://localhost:5000`
   - Admin dashboard: `http://localhost:5000/admin`

3. **Admin Setup**
   - Use the email configured in your `.env` file to access the admin dashboard
   - Default template email: `admin@access.com`

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SUPABASE_URL` | Your Supabase project URL | Yes |
| `SUPABASE_ANON_KEY` | Your Supabase anonymous key | Yes |
| `SESSION_SECRET` | Secret key for Flask sessions | Yes |
| `ADMIN_EMAIL` | Email address for admin access | Yes |

### Service Configuration

Services support two account types:

1. **Credentials**: Traditional username/password accounts
2. **Cookies**: Browser cookie data for authenticated sessions

### Field Customization

Each service can have customized field labels through the admin settings:
- Username/Email field label
- Password field label  
- Expiry field label
- Additional field label

## File Structure

```
streambase/
├── app.py                          # Main Flask application
├── .env                           # Environment variables (not in repo)
├── .env.template                  # Environment template
├── requirements.txt               # Python dependencies
├── static/                        # Static assets
│   ├── css/style.css             # Main stylesheet
│   ├── js/main.js                # JavaScript functionality
│   └── walter-white.gif          # Static assets
├── templates/                     # Jinja2 templates
│   ├── base.html                 # Base template
│   ├── index.html                # Homepage
│   ├── service.html              # Service detail page
│   ├── admin_login.html          # Admin login
│   ├── admin_dashboard.html      # Admin dashboard
│   ├── admin_service_form.html   # Service creation/editing
│   └── admin_service_settings.html # Service settings
└── README.md                      # This file
```

## Features Overview

### Public Interface
- Browse available OTT services
- View account counts and types
- Access accounts/cookies with one-click selection
- Responsive design with theme toggle

### Admin Dashboard
- Add/edit/delete services
- Upload custom service icons
- Configure service colors and branding
- Manage account data (credentials or cookies)
- Per-service settings configuration
- Account status management

### Security Features
- Session-based admin authentication
- Environment variable configuration
- Secure file upload handling
- Input validation and sanitization

## Browser Support

- Chrome 80+
- Firefox 75+
- Safari 13+
- Edge 80+

## Contact
-- Discord : @heisenburger_7
-- Kiny send me message if you encounter any bugs or any problems

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions, please open an issue in the GitHub repository.
