# iPayslip

A comprehensive payroll management system built with Django that supports employee management, payroll processing, loan management with automatic deductions, payslip generation, and role-based access control.

## Features

- **Employee Management**: Add, edit, and manage employee information
- **Payroll Processing**: Generate and manage payroll records with automatic calculations
- **Tax Calculation**: Tiered tax calculation based on configurable tax brackets
- **Loan Management**: Track employee loans and automatic deductions from payroll
- **Payslip Generation**: Generate professional PDF payslips for employees
- **Role-Based Access Control**: Secure access based on user roles and permissions

## Technology Stack

- **Backend**: Django 4.2+
- **Database**: SQLite (development) / PostgreSQL (production)
- **Authentication**: Django-allauth
- **Frontend**: Bootstrap 5
- **PDF Generation**: ReportLab/xhtml2pdf
- **Task Scheduling**: Celery (for automated tasks)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/payslip.git
   cd payslip
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Apply migrations:
   ```
   python manage.py migrate
   ```

5. Create a superuser:
   ```
   python manage.py create_superuser
   ```

6. Run the development server:
   ```
   python manage.py runserver
   ```

7. Access the application at http://127.0.0.1:8000/

## Initial Setup

1. Create payroll periods using the management command:
   ```
   python manage.py create_payroll_period
   ```

2. Create tax tiers for income tax calculation:
   ```
   python manage.py create_tax_tiers
   ```

## Usage

1. **Employee Management**:
   - Add employees with their personal and financial information
   - Manage departments and positions

2. **Payroll Processing**:
   - Create payroll periods
   - Process payroll for all employees or individually
   - Add custom earnings and deductions

3. **Tax Management**:
   - Configure tax tiers for progressive taxation
   - Automatic tax calculation during payroll processing

4. **Loan Management**:
   - Create loan types with different interest rates and terms
   - Process loan applications and approvals
   - Track loan repayments and balances

5. **Reporting**:
   - Generate individual payslips as PDFs
   - View payroll summaries and reports

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please ensure your code follows the project's coding style and includes appropriate tests.

## License

This project is licensed under the Creative Commons Attribution-NonCommercial 4.0 International License - see the [LICENSE](LICENSE) file for details.

You are free to:
- Share — copy and redistribute the material in any medium or format
- Adapt — remix, transform, and build upon the material

Under the following terms:
- Attribution — You must give appropriate credit, provide a link to the license, and indicate if changes were made.
- NonCommercial — You may not use the material for commercial purposes.

## Contact

For any questions or support, please open an issue on GitHub or contact the maintainers directly. 