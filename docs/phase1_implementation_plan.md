# Phase 1 Implementation Plan: Employee and Manager Roles

## 1. Role Definition

For the initial implementation, we will focus on just two roles:

1. **Manager Role**
   - Equivalent to superuser with full system access
   - Can view and manage all employees, payrolls, loans, and leave requests
   - Has access to all administrative functions

2. **Employee Role**
   - Can only view and manage their own data
   - Limited to CRUD operations on their own requests (loans, leaves)
   - No access to other employees' data or administrative functions

## 2. Dashboard Components Visibility

### 2.1 Employee Portal Dashboard

| Component/Widget               | Manager | Employee |
|--------------------------------|---------|----------|
| Personal Information           | ✓       | ✓        |
| Personal Recent Payrolls       | ✓       | ✓        |
| Personal Active Loans          | ✓       | ✓        |
| Personal Leave Requests        | ✓       | ✓        |
| All Employees List             | ✓       | ✗        |
| All Payrolls                   | ✓       | ✗        |
| All Loan Requests              | ✓       | ✗        |
| All Leave Requests             | ✓       | ✗        |
| System Statistics              | ✓       | ✗        |
| Admin Portal Link              | ✓       | ✗        |

### 2.2 Navigation Bar

| Navigation Item                | Manager | Employee |
|--------------------------------|---------|----------|
| Dashboard                      | ✓       | ✓        |
| Employees                      | ✓       | ✗        |
| Payroll Dropdown               | ✓       | ✗        |
| Loans                          | ✓       | ✗        |
| Admin Portal                   | ✓       | ✗        |
| My Payrolls                    | ✓       | ✓        |
| My Loans                       | ✓       | ✓        |
| My Leave Requests              | ✓       | ✓        |

## 3. Implementation Steps

### 3.1 Database Updates

1. **Update UserRole Model**:
   - Ensure there are two predefined roles: "Manager" and "Employee"
   - Set appropriate permissions for each role

2. **Assign Roles to Users**:
   - Assign "Manager" role to all superusers
   - Assign "Employee" role to all other users with employee profiles

### 3.2 Access Control Implementation

1. **Create Role-Based Mixins**:
   ```python
   # In a new file: user_management/mixins.py
   
   from django.contrib.auth.mixins import UserPassesTestMixin
   from django.shortcuts import redirect
   from user_management.models import UserProfile
   
   class ManagerRequiredMixin(UserPassesTestMixin):
       """Mixin to ensure only managers can access the view"""
       def test_func(self):
           if not self.request.user.is_authenticated:
               return False
           return self.request.user.is_superuser
       
       def handle_no_permission(self):
           return redirect('employee_dashboard')
   
   class EmployeeAccessMixin(UserPassesTestMixin):
       """Mixin to ensure users can only access their own employee data"""
       def test_func(self):
           if not self.request.user.is_authenticated:
               return False
           
           # Get the object that the view is displaying
           obj = self.get_object()
           
           # Check if the object belongs to the current user
           if hasattr(obj, 'employee'):
               if hasattr(obj.employee, 'user'):
                   return obj.employee.user == self.request.user
               return obj.employee == self.request.user
           elif hasattr(obj, 'user'):
               return obj.user == self.request.user
           
           return False
       
       def handle_no_permission(self):
           return redirect('employee_dashboard')
   ```

2. **Update Views**:
   - Apply the appropriate mixins to all views
   - Ensure employee views only show the user's own data

### 3.3 Template Updates

1. **Update Base Template**:
   ```html
   <!-- In templates/base.html -->
   
   <ul class="navbar-nav me-auto">
       {% if user.is_authenticated %}
           <li class="nav-item">
               <a class="nav-link {% if request.path == '/my/' %}active{% endif %}" href="{% url 'employee_dashboard' %}">Dashboard</a>
           </li>
           
           {% if user.is_superuser %}
               <li class="nav-item">
                   <a class="nav-link {% if 'employees' in request.path %}active{% endif %}" href="{% url 'employee_list' %}">Employees</a>
               </li>
               <li class="nav-item dropdown">
                   <a class="nav-link dropdown-toggle {% if 'payroll' in request.path %}active{% endif %}" href="#" id="payrollDropdown" role="button" data-bs-toggle="dropdown" aria-expanded="false">
                       Payroll
                   </a>
                   <ul class="dropdown-menu" aria-labelledby="payrollDropdown">
                       <li><a class="dropdown-item" href="{% url 'payroll_list' %}">Payroll List</a></li>
                       <li><a class="dropdown-item" href="{% url 'process_payroll' %}">Process Payroll</a></li>
                       <li><hr class="dropdown-divider"></li>
                       <li><a class="dropdown-item" href="{% url 'period_list' %}">Payroll Periods</a></li>
                       <li><a class="dropdown-item" href="{% url 'item_list' %}">Standard Items</a></li>
                       <li><a class="dropdown-item" href="{% url 'tax_tier_list' %}">Tax Tiers</a></li>
                   </ul>
               </li>
               <li class="nav-item">
                   <a class="nav-link {% if 'loans' in request.path %}active{% endif %}" href="{% url 'loan_list' %}">Loans</a>
               </li>
           {% endif %}
           
           <!-- Employee-specific navigation items -->
           <li class="nav-item">
               <a class="nav-link {% if 'my/payrolls' in request.path %}active{% endif %}" href="{% url 'employee_payroll_list' %}">My Payrolls</a>
           </li>
           <li class="nav-item">
               <a class="nav-link {% if 'my/loans' in request.path %}active{% endif %}" href="{% url 'employee_loan_list' %}">My Loans</a>
           </li>
           <li class="nav-item">
               <a class="nav-link {% if 'my/leaves' in request.path %}active{% endif %}" href="{% url 'employee_leave_request_list' %}">My Leave Requests</a>
           </li>
       {% endif %}
   </ul>
   ```

2. **Update Dashboard Template**:
   ```html
   <!-- In templates/employee_portal/dashboard.html -->
   
   {% extends "base.html" %}
   {% load i18n %}
   {% load django_bootstrap5 %}
   
   {% block title %}{% trans "Dashboard" %} | iPaySlip{% endblock %}
   
   {% block content %}
   <div class="container py-4">
       <div class="row mb-4">
           <div class="col-12">
               <div class="card border-0 shadow-sm">
                   <div class="card-body">
                       <h1 class="h3 mb-3">{% trans "Welcome" %}, {{ employee.full_name }}</h1>
                       <p class="text-muted">{% trans "Employee ID" %}: {{ employee.employee_id }}</p>
                       <p class="text-muted">{% trans "Department" %}: {{ employee.department|default:"Not assigned" }}</p>
                       <p class="text-muted">{% trans "Position" %}: {{ employee.position|default:"Not assigned" }}</p>
                   </div>
               </div>
           </div>
       </div>
       
       <!-- Personal Data Widgets - Visible to All -->
       <div class="row mb-4">
           <div class="col-md-4 mb-4 mb-md-0">
               <div class="card border-0 shadow-sm h-100">
                   <div class="card-header bg-primary text-white">
                       <div class="d-flex justify-content-between align-items-center">
                           <h5 class="mb-0">{% trans "Recent Payrolls" %}</h5>
                           <a href="{% url 'employee_payroll_list' %}" class="btn btn-sm btn-light">{% trans "View All" %}</a>
                       </div>
                   </div>
                   <div class="card-body">
                       {% if recent_payrolls %}
                           <!-- Payroll list content -->
                       {% else %}
                           <p class="text-muted text-center my-3">{% trans "No payroll records found." %}</p>
                       {% endif %}
                   </div>
               </div>
           </div>
           
           <div class="col-md-4 mb-4 mb-md-0">
               <div class="card border-0 shadow-sm h-100">
                   <div class="card-header bg-success text-white">
                       <div class="d-flex justify-content-between align-items-center">
                           <h5 class="mb-0">{% trans "Active Loans" %}</h5>
                           <a href="{% url 'employee_loan_list' %}" class="btn btn-sm btn-light">{% trans "View All" %}</a>
                       </div>
                   </div>
                   <div class="card-body">
                       {% if active_loans %}
                           <!-- Loan list content -->
                       {% else %}
                           <p class="text-muted text-center my-3">{% trans "No active loans." %}</p>
                       {% endif %}
                       <div class="mt-3">
                           <a href="{% url 'employee_loan_request' %}" class="btn btn-outline-success btn-sm w-100">
                               <i class="bi bi-plus-circle me-1"></i> {% trans "Request New Loan" %}
                           </a>
                       </div>
                   </div>
               </div>
           </div>
           
           <div class="col-md-4">
               <div class="card border-0 shadow-sm h-100">
                   <div class="card-header bg-info text-white">
                       <div class="d-flex justify-content-between align-items-center">
                           <h5 class="mb-0">{% trans "Leave Requests" %}</h5>
                           <a href="{% url 'employee_leave_request_list' %}" class="btn btn-sm btn-light">{% trans "View All" %}</a>
                       </div>
                   </div>
                   <div class="card-body">
                       {% if recent_leave_requests %}
                           <!-- Leave request list content -->
                       {% else %}
                           <p class="text-muted text-center my-3">{% trans "No leave requests found." %}</p>
                       {% endif %}
                       <div class="mt-3">
                           <a href="{% url 'employee_leave_request_create' %}" class="btn btn-outline-info btn-sm w-100">
                               <i class="bi bi-plus-circle me-1"></i> {% trans "Request Leave" %}
                           </a>
                       </div>
                   </div>
               </div>
           </div>
       </div>
       
       <!-- Manager-Only Widgets -->
       {% if user.is_superuser %}
       <div class="row mb-4">
           <div class="col-12 mb-4">
               <div class="card border-0 shadow-sm">
                   <div class="card-header bg-dark text-white">
                       <h5 class="mb-0">{% trans "System Overview" %}</h5>
                   </div>
                   <div class="card-body">
                       <div class="row">
                           <div class="col-md-3 mb-3 mb-md-0">
                               <div class="card bg-primary text-white">
                                   <div class="card-body text-center">
                                       <h1 class="display-4">{{ employee_count }}</h1>
                                       <p class="mb-0">{% trans "Employees" %}</p>
                                   </div>
                               </div>
                           </div>
                           <div class="col-md-3 mb-3 mb-md-0">
                               <div class="card bg-success text-white">
                                   <div class="card-body text-center">
                                       <h1 class="display-4">{{ payroll_count }}</h1>
                                       <p class="mb-0">{% trans "Payrolls" %}</p>
                                   </div>
                               </div>
                           </div>
                           <div class="col-md-3 mb-3 mb-md-0">
                               <div class="card bg-warning text-white">
                                   <div class="card-body text-center">
                                       <h1 class="display-4">{{ loan_count }}</h1>
                                       <p class="mb-0">{% trans "Loans" %}</p>
                                   </div>
                               </div>
                           </div>
                           <div class="col-md-3">
                               <div class="card bg-info text-white">
                                   <div class="card-body text-center">
                                       <h1 class="display-4">{{ leave_count }}</h1>
                                       <p class="mb-0">{% trans "Leaves" %}</p>
                                   </div>
                               </div>
                           </div>
                       </div>
                   </div>
               </div>
           </div>
           
           <div class="col-md-6 mb-4 mb-md-0">
               <div class="card border-0 shadow-sm h-100">
                   <div class="card-header bg-warning text-white">
                       <div class="d-flex justify-content-between align-items-center">
                           <h5 class="mb-0">{% trans "Pending Loan Requests" %}</h5>
                           <a href="{% url 'loan_list' %}" class="btn btn-sm btn-light">{% trans "View All" %}</a>
                       </div>
                   </div>
                   <div class="card-body">
                       {% if pending_loans %}
                           <div class="list-group list-group-flush">
                               {% for loan in pending_loans %}
                                   <a href="{% url 'loan_detail' loan.id %}" class="list-group-item list-group-item-action">
                                       <div class="d-flex w-100 justify-content-between">
                                           <h6 class="mb-1">{{ loan.employee.full_name }}</h6>
                                           <small>{{ loan.request_date|date:"M d, Y" }}</small>
                                       </div>
                                       <p class="mb-1">{% trans "Amount" %}: {{ loan.amount }} {{ loan.currency.code }}</p>
                                   </a>
                               {% endfor %}
                           </div>
                       {% else %}
                           <p class="text-muted text-center my-3">{% trans "No pending loan requests." %}</p>
                       {% endif %}
                   </div>
               </div>
           </div>
           
           <div class="col-md-6">
               <div class="card border-0 shadow-sm h-100">
                   <div class="card-header bg-danger text-white">
                       <div class="d-flex justify-content-between align-items-center">
                           <h5 class="mb-0">{% trans "Pending Leave Requests" %}</h5>
                           <a href="#" class="btn btn-sm btn-light">{% trans "View All" %}</a>
                       </div>
                   </div>
                   <div class="card-body">
                       {% if pending_leaves %}
                           <div class="list-group list-group-flush">
                               {% for leave in pending_leaves %}
                                   <a href="#" class="list-group-item list-group-item-action">
                                       <div class="d-flex w-100 justify-content-between">
                                           <h6 class="mb-1">{{ leave.employee.get_full_name }}</h6>
                                           <small>{{ leave.created_at|date:"M d, Y" }}</small>
                                       </div>
                                       <p class="mb-1">{{ leave.get_leave_type_display }}: {{ leave.start_date|date:"M d" }} - {{ leave.end_date|date:"M d, Y" }}</p>
                                   </a>
                               {% endfor %}
                           </div>
                       {% else %}
                           <p class="text-muted text-center my-3">{% trans "No pending leave requests." %}</p>
                       {% endif %}
                   </div>
               </div>
           </div>
       </div>
       {% endif %}
   </div>
   {% endblock %}
   ```

## 4. View Updates for Employee Dashboard

```python
@login_required
def employee_dashboard(request):
    """Dashboard view for employee portal"""
    try:
        # Get the employee associated with the current user
        employee = Employee.objects.get(user=request.user)
        
        # Get recent payrolls
        recent_payrolls = Payroll.objects.filter(employee=employee).order_by('-period__payment_date')[:5]
        
        # Get active loans
        active_loans = Loan.objects.filter(employee=employee, status='active').order_by('-request_date')
        
        # Get recent leave requests
        recent_leave_requests = Leave.objects.filter(employee=request.user).order_by('-created_at')[:5]
        
        context = {
            'employee': employee,
            'recent_payrolls': recent_payrolls,
            'active_loans': active_loans,
            'recent_leave_requests': recent_leave_requests,
        }
        
        # Add manager-only context data
        if request.user.is_superuser:
            employee_count = Employee.objects.count()
            payroll_count = Payroll.objects.count()
            loan_count = Loan.objects.count()
            leave_count = Leave.objects.count()
            
            pending_loans = Loan.objects.filter(status='pending').order_by('-request_date')[:5]
            pending_leaves = Leave.objects.filter(status='pending').order_by('-created_at')[:5]
            
            context.update({
                'employee_count': employee_count,
                'payroll_count': payroll_count,
                'loan_count': loan_count,
                'leave_count': leave_count,
                'pending_loans': pending_loans,
                'pending_leaves': pending_leaves,
            })
        
        return render(request, 'employee_portal/dashboard.html', context)
    except Employee.DoesNotExist:
        messages.error(request, "You don't have an employee profile in the system.")
        return redirect('home')
```

## 5. Testing Plan

1. **Test as Manager**:
   - Log in as a superuser
   - Verify all widgets are visible
   - Verify access to all system features

2. **Test as Employee**:
   - Log in as a regular employee
   - Verify only personal data widgets are visible
   - Verify no access to administrative features
   - Verify CRUD operations on own requests work properly

## 6. Next Steps

After implementing Phase 1, we will:

1. Gather feedback from users
2. Refine the implementation as needed
3. Proceed to more advanced role-based access control if required
