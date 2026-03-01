import os
import re
import time
import resend
from flask import Flask, request, redirect, send_from_directory, jsonify
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


def validate_phone(phone_raw):
    """Validate and normalize a North American phone number.
    Returns (normalized_digits, error_message). error_message is None if valid."""
    digits = re.sub(r'\D', '', phone_raw)

    # Strip leading country code 1
    if len(digits) == 11 and digits.startswith('1'):
        digits = digits[1:]

    if len(digits) != 10:
        return None, 'Phone number must be 10 digits'

    # NANP rules: area code and exchange cannot start with 0 or 1
    if digits[0] in ('0', '1'):
        return None, f'Invalid area code ({digits[:3]}). Please double-check your phone number'
    if digits[3] in ('0', '1'):
        return None, 'Invalid phone number. Please double-check your number'

    return digits, None


app = Flask(__name__, static_folder='../frontend', static_url_path='')

resend.api_key = os.environ.get('RESEND_API_KEY')
NOTIFICATION_EMAIL = 'torsten@stonesharp.academy'
EMAIL_FROM = os.environ.get('EMAIL_FROM', 'noreply@stonesharpacademy.com')

# Cache-bust version — regenerated on every deploy
DEPLOY_VERSION = str(int(time.time()))

# Database setup
DATABASE_URL = os.environ.get('DATABASE_URL')
Base = declarative_base()


class Lead(Base):
    __tablename__ = 'leads'

    id = Column(Integer, primary_key=True)
    full_name = Column(String(255))
    email = Column(String(255))
    phone = Column(String(50))
    grade = Column(String(50))
    course = Column(String(255))
    message = Column(Text)
    source = Column(String(50))
    submitted_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Lead(name='{self.full_name}', email='{self.email}')>"


# Initialize database connection if DATABASE_URL exists
db_session = None
if DATABASE_URL:
    try:
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)
        db_session = Session()
        print("Database connection established")
    except Exception as e:
        print(f"Database connection failed: {e}")
        db_session = None


@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/favicon.ico')
def favicon():
    return redirect('/assets/logo.svg', code=301)


@app.route('/<path:path>')
def static_files(path):
    return send_from_directory(app.static_folder, path)


@app.after_request
def cache_bust_html(response):
    if response.content_type and 'text/html' in response.content_type:
        data = response.get_data(as_text=True)
        data = data.replace('.js"', f'.js?v={DEPLOY_VERSION}"')
        data = data.replace('.css"', f'.css?v={DEPLOY_VERSION}"')
        response.set_data(data)
    return response


@app.route('/submit', methods=['POST'])
def submit_form():
    try:
        # Get form data
        data = request.form
        full_name = data.get('name', 'N/A')
        email = data.get('email', 'N/A')
        phone_raw = data.get('phone', '')
        grade = data.get('grade', '')
        message = data.get('message', '')

        # Validate required fields
        if not full_name or full_name == 'N/A':
            if request.headers.get('Accept') == 'application/json':
                return jsonify({"error": "Name is required"}), 400
            return redirect('/contact.html')
        if not email or '@' not in email:
            if request.headers.get('Accept') == 'application/json':
                return jsonify({"error": "A valid email is required"}), 400
            return redirect('/contact.html')
        if not message.strip():
            if request.headers.get('Accept') == 'application/json':
                return jsonify({"error": "Message is required"}), 400
            return redirect('/contact.html')

        # Validate phone number (optional field on contact form)
        phone = ''
        if phone_raw.strip():
            phone_digits, phone_error = validate_phone(phone_raw)
            if phone_error:
                if request.headers.get('Accept') == 'application/json':
                    return jsonify({"error": phone_error}), 400
                return redirect('/contact.html')
            phone = f'({phone_digits[:3]}) {phone_digits[3:6]}-{phone_digits[6:]}'

        # Save to database if available
        if db_session:
            try:
                lead = Lead(
                    full_name=full_name,
                    email=email,
                    phone=phone,
                    grade=grade,
                    message=message,
                    source='main-website'
                )
                db_session.add(lead)
                db_session.commit()
                print(f"Lead saved to database: {full_name} ({email})")
            except Exception as db_error:
                print(f"Database error: {db_error}")
                db_session.rollback()

        # Build email HTML
        html_content = f"""
        <h2>New Contact Form Submission - Stone Sharp Academy</h2>
        <p><em>From: Main Website</em></p>
        <table style="border-collapse: collapse; width: 100%;">
            <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Name</strong></td><td style="padding: 8px; border: 1px solid #ddd;">{full_name}</td></tr>
            <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Email</strong></td><td style="padding: 8px; border: 1px solid #ddd;">{email}</td></tr>
            <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Phone</strong></td><td style="padding: 8px; border: 1px solid #ddd;">{phone or 'Not provided'}</td></tr>
            <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Grade</strong></td><td style="padding: 8px; border: 1px solid #ddd;">{grade or 'Not selected'}</td></tr>
            <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Message</strong></td><td style="padding: 8px; border: 1px solid #ddd;">{message}</td></tr>
        </table>
        """

        # Send email via Resend
        try:
            resend.Emails.send({
                "from": EMAIL_FROM,
                "to": NOTIFICATION_EMAIL,
                "subject": f"New Contact Form Message - {full_name}",
                "html": html_content,
                "reply_to": email if email != 'N/A' and '@' in email else None
            })
            print(f"Email sent successfully for: {full_name} ({email})")
        except Exception as email_error:
            print(f"Email sending error: {email_error}")

        # Return success for AJAX
        if request.headers.get('Accept') == 'application/json':
            return jsonify({"success": True})

        return redirect('/contact.html')

    except Exception as e:
        print(f"Error: {e}")
        if request.headers.get('Accept') == 'application/json':
            return jsonify({"error": str(e)}), 500
        return redirect('/contact.html')


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
