# Role-Based Access Control Analysis for iPaySlip System

## 1. Introduction

This document outlines the role-based access control (RBAC) system for the iPaySlip application. The goal is to ensure that users only have access to the features and data that are relevant to their role within the organization, enhancing both security and user experience.

## 2. Current System Analysis

### 2.1 Existing Roles

The current system has the following implicit roles:

1. **Superuser/Admin**: Full access to all system features and data
2. **Staff**: Access to the Django admin interface and potentially other administrative features
3. **Employee**: Access to personal data, payroll history, loan requests, and leave requests

### 2.2 Current Access Control Implementation

The current implementation uses:

- `LoginRequiredMixin` for basic authentication
- `UserPassesTestMixin` for role-based authorization
- Custom `EmployeeAccessMixin` to ensure employees can only access their own data
- `@user_passes_test(is_superuser)` for admin-only views

### 2.3 Current Issues

1. **Navigation Bar Access**: All authenticated users see the same navigation options regardless of role
2. **Widget Visibility**: Employees see widgets that may not be relevant to them
3. **Role Granularity**: Limited role definitions without fine-grained permissions
4. **Inconsistent Access Control**: Some views use mixins, others use decorators

## 3. Proposed Role Structure

### 3.1 Core Roles

1. **System Administrator**
   - Manages system configuration, user accounts, and roles
   - Has access to all system features and data
   - Can perform database maintenance and system backups

2. **HR Manager**
   - Manages employee records
   - Processes payroll
   - Reviews and approves/rejects loan requests and leave requests
   - Access to reports and analytics

3. **Finance Manager**
   - Manages financial aspects (payroll, loans, etc.)
   - Access to financial reports and analytics
   - Cannot modify employee personal information

4. **Department Manager**
   - Manages employees within their department
   - Reviews and approves/rejects leave requests for their department
   - Limited access to payroll information

5. **Employee**
   - Views personal information
   - Views personal payroll history
   - Submits and tracks loan requests
   - Submits and tracks leave requests

### 3.2 Permission Matrix

| Feature/Action                   | System Admin | HR Manager | Finance Manager | Department Manager | Employee |
|----------------------------------|--------------|------------|-----------------|-------------------|----------|
| **User Management**              |              |            |                 |                   |          |
| Create/Edit User Accounts        | ✓            | ✓          | ✗               | ✗                 | ✗        |
| Assign Roles                     | ✓            | ✗          | ✗               | ✗                 | ✗        |
| **Employee Management**          |              |            |                 |                   |          |
| View All Employees               | ✓            | ✓          | ✓               | ✗                 | ✗        |
| View Department Employees        | ✓            | ✓          | ✓               | ✓                 | ✗        |
| Create/Edit Employee Records     | ✓            | ✓          | ✗               | ✗                 | ✗        |
| View Own Employee Record         | ✓            | ✓          | ✓               | ✓                 | ✓        |
| **Payroll Management**           |              |            |                 |                   |          |
| Process Payroll                  | ✓            | ✓          | ✓               | ✗                 | ✗        |
| View All Payroll Records         | ✓            | ✓          | ✓               | ✗                 | ✗        |
| View Department Payroll Summary  | ✓            | ✓          | ✓               | ✓                 | ✗        |
| View Own Payroll Records         | ✓            | ✓          | ✓               | ✓                 | ✓        |
| **Loan Management**              |              |            |                 |                   |          |
| Configure Loan Types             | ✓            | ✓          | ✓               | ✗                 | ✗        |
| Approve/Reject Loan Requests     | ✓            | ✓          | ✓               | ✗                 | ✗        |
| View All Loan Requests           | ✓            | ✓          | ✓               | ✗                 | ✗        |
| View Own Loan Requests           | ✓            | ✓          | ✓               | ✓                 | ✓        |
| Submit Loan Request              | ✓            | ✓          | ✓               | ✓                 | ✓        |
| **Leave Management**             |              |            |                 |                   |          |
| Configure Leave Types            | ✓            | ✓          | ✗               | ✗                 | ✗        |
| Approve/Reject All Leave Requests| ✓            | ✓          | ✗               | ✗                 | ✗        |
| Approve/Reject Department Leaves | ✓            | ✓          | ✗               | ✓                 | ✗        |
| View All Leave Requests          | ✓            | ✓          | ✗               | ✗                 | ✗        |
| View Department Leave Requests   | ✓            | ✓          | ✗               | ✓                 | ✗        |
| View Own Leave Requests          | ✓            | ✓          | ✓               | ✓                 | ✓        |
| Submit Leave Request             | ✓            | ✓          | ✓               | ✓                 | ✓        |
| **Reports & Analytics**          |              |            |                 |                   |          |
| System-wide Reports              | ✓            | ✓          | ✓               | ✗                 | ✗        |
| Department Reports               | ✓            | ✓          | ✓               | ✓                 | ✗        |
| Personal Reports                 | ✓            | ✓          | ✓               | ✓                 | ✓        |

## 4. Implementation Plan

### 4.1 Database Changes

1. Utilize the existing `UserRole` and `UserProfile` models
2. Add predefined roles with appropriate permissions
3. Ensure each user has a role assigned

### 4.2 Access Control Implementation

1. Create role-based mixins for each role type
2. Implement permission checking based on the user's role
3. Update views to use the appropriate mixins

### 4.3 UI Changes

1. Modify navigation bar to show only relevant links based on user role
2. Update dashboard widgets to display only relevant information
3. Create role-specific dashboards

### 4.4 Widget Visibility Control

#### 4.4.1 Employee Portal Dashboard

| Widget                | System Admin | HR Manager | Finance Manager | Department Manager | Employee |
|-----------------------|--------------|------------|-----------------|-------------------|----------|
| Employee Information  | ✓            | ✓          | ✓               | ✓                 | ✓        |
| Recent Payrolls       | ✓            | ✓          | ✓               | ✓                 | ✓        |
| Active Loans          | ✓            | ✓          | ✓               | ✓                 | ✓        |
| Leave Requests        | ✓            | ✓          | ✓               | ✓                 | ✓        |
| All Employees Widget  | ✓            | ✓          | ✓               | ✓                 | ✗        |
| Department Employees  | ✓            | ✓          | ✓               | ✓                 | ✗        |
| Company-wide Loans    | ✓            | ✓          | ✓               | ✗                 | ✗        |
| Company-wide Leaves   | ✓            | ✓          | ✗               | ✗                 | ✗        |

#### 4.4.2 Admin Portal Dashboard

| Widget                | System Admin | HR Manager | Finance Manager | Department Manager | Employee |
|-----------------------|--------------|------------|-----------------|-------------------|----------|
| Employee Statistics   | ✓            | ✓          | ✓               | ✓                 | ✗        |
| Payroll Statistics    | ✓            | ✓          | ✓               | ✓                 | ✗        |
| Loan Statistics       | ✓            | ✓          | ✓               | ✗                 | ✗        |
| Leave Statistics      | ✓            | ✓          | ✓               | ✓                 | ✗        |
| System Logs           | ✓            | ✗          | ✗               | ✗                 | ✗        |

## 5. Implementation Steps

### Phase 1: Role Definition and Assignment

1. Define roles in the database
2. Assign roles to existing users
3. Update user creation process to include role assignment

### Phase 2: Access Control Logic

1. Create role-based permission mixins
2. Update views to use the appropriate mixins
3. Implement permission checking in templates

### Phase 3: UI Updates

1. Update navigation bar to show role-specific links
2. Create role-specific dashboards
3. Update widget visibility based on user role

### Phase 4: Testing and Refinement

1. Test with users of different roles
2. Gather feedback and refine permissions
3. Document the final role-based access control system

## 6. Conclusion

Implementing this role-based access control system will enhance both security and user experience in the iPaySlip application. By ensuring users only see and access what's relevant to their role, we can streamline workflows and reduce confusion while maintaining proper data security.
