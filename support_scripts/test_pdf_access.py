import requests

# Start a session to maintain cookies
session = requests.Session()

# Login to the application
login_url = 'http://localhost:8000/accounts/login/'
login_data = {
    'login': 'admin',
    'password': 'admin123',
    'csrfmiddlewaretoken': ''
}

# First get the login page to extract CSRF token
response = session.get(login_url)
if 'csrftoken' in session.cookies:
    login_data['csrfmiddlewaretoken'] = session.cookies['csrftoken']

# Perform login
response = session.post(login_url, data=login_data, headers={'Referer': login_url})
print(f'Login status code: {response.status_code}')

# Try to access the PDF endpoint
pdf_url = 'http://localhost:8000/payroll/1/pdf/'
response = session.get(pdf_url)
print(f'PDF endpoint status code: {response.status_code}')

# If successful, save the PDF
if response.status_code == 200:
    with open('payslip.pdf', 'wb') as f:
        f.write(response.content)
    print('PDF saved as payslip.pdf')
else:
    print(f'Failed to get PDF: {response.text[:500]}') 