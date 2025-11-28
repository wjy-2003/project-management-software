# DevTeamFlow High-Level Design Document

## 1. Introduction

### 1.1 Project Overview
DevTeamFlow is a code project management plugin based on Scrum principles, designed to optimize code project development workflows. It provides project management, team collaboration, requirement tracking, and progress visualization capabilities. Through centralized defect management, full-lifecycle requirement tracking, and cross-project resource allocation, the system addresses issues such as inadequate project health monitoring, version control problems caused by manual requirement management, and uneven human resource distribution.

### 1.2 Objectives
- Provide project managers with real-time project health monitoring and full-lifecycle requirement management.
- Equip team leads with efficient task assignment and code verification tools.
- Equip business analysts with requirements management and environment dependency handling capabilities.
- Empower portfolio managers with cross-project resource optimization and progress visualization.
- Offer developers real-time collaborative coding and code history tracing.

### 1.3 Technology Stack
- **Backend**: Django (Python framework providing web services and business logic processing)
- **Frontend**: HTML + CSS (for page display and interaction, integrated with Django templates)
- **Database**: SQLite (lightweight database for storing projects, requirements, teams, etc.)
- **Caching**: Redis (optional, for session management and data synchronization optimization)
- **Other**: Git (for version control and branch management), VSCode Web (supports real-time collaborative coding)

## 2. System Architecture

### 2.1 Overall Architecture
DevTeamFlow adopts a frontend-backend separated MVC architecture built on the Django framework. The frontend implements the user interface via HTML and CSS, while the backend handles business logic and data operations. SQLite stores persistent data, and Redis (optional) is used for caching and session management. The system interacts with the frontend via RESTful APIs and supports Git integration for version control.

**Architectural Layers**:
- **Presentation Layer**: HTML + CSS, rendering dashboards, Gantt charts, burn-down charts, and other visual interfaces.
- **Business Logic Layer**: Django backend, handling project management, requirement tracking, permission control, and other logic.
- **Data Access Layer**: SQLite database stores project, requirement, and team member data; Redis handles caching and sessions.
- **External Integrations**: Git integration for branch management and commit history tracking; VSCode Web API for real-time collaborative coding.

### 2.2 Module Division
The system is divided into the following core modules:
1. **Project Management Module**:
   - Functions: Project configuration, full lifecycle requirement management, environment dependency checks.
   - Responsibilities: Manage project information, requirement statuses, branch operations, and dependency package conflict resolution.
2. **Visualization Module**:
   - Functions: Project dashboards, Gantt charts, burn-down charts.
   - Responsibilities: Display project progress, health metrics, and timelines.
3. **Team Management Module**:
   - Functions: Team member profile management, role-based access control, cross-project task assignment.
   - Responsibilities: Maintain team information, permission configurations, and task allocation.
4. **Git Integration Module**:
   - Functions: Commit history display, graphical operations, conflict resolution.
   - Purpose: Integrates Git systems, displays hierarchical commit history, flags conflicts, and supports VSCode opening for resolution.
5. **Real-Time Collaboration Module**:
   - Features: Supports VSCode Web real-time collaboration, session security controls, data synchronization.
   - Purpose: Provides collaborative coding environments with 30-minute session timeouts for inactivity, ensuring local-to-cloud data synchronization.

## 3. Feature Design

### 3.1 Project Management
- **Project Setup**: Manage project information via Django models, supporting CRUD operations (Create, Read, Update, Delete).
- **Requirement Management**:
  - Supports full lifecycle status management for requirements (New → In Progress → Implemented → Closed).
  - Provides API for CRUD operations on requirements, including linking to Git branches and documentation.
  - Integrates Git command-line tools (e.g., `git branch`, `git tag`) for branch management.
- **Environment Dependency Management**:
  - Automatically detects dependency conflicts by analyzing dependencies via Python scripts calling `pipdeptree` or similar tools.
  - Support environment template configuration stored in an SQLite database.

### 3.2 Visualization
- **Dashboard**: Implement dynamic dashboards using Django templates and CSS to display Gantt charts and burn-down charts.
- **Gantt Chart**: Visualize project task and requirement progress along a timeline using open-source libraries (e.g., Chart.js).
- **Burn-down Charts**: Visualize remaining work versus time, with real-time updates.

### 3.3 Team Management
- **Member Profiles**: Perform CRUD operations on member information via Django Admin or custom interfaces.
- **Permission Control**: Implement role-based access control using Django's built-in authentication and permissions system (`django.contrib.auth`).
- **Cross-Project Assignments**: Optimizes member assignments via database queries, supporting multi-project task allocation.

### 3.4 Git Integration
- **Commit History**: Retrieves commit records using the GitPython library, generating a tree-structured display.
- **Graphical Operations**: Executes Git commands (e.g., `git merge`, `git rebase`) via the frontend interface, with conflict alerts.
- **Conflict Resolution**: Detect merge conflicts and open local files for editing via the VSCode Web API.

### 3.5 Real-Time Collaboration
- **Pair Coding**: Integrate VSCode Web for multi-user real-time coding, with data synchronization via WebSocket.
- **Session Security**: Manage sessions using Redis with a 30-minute timeout mechanism.
- **Data Synchronization**: Utilizes Django Channels (Redis-based) for real-time synchronization between local and cloud data.

## 4. Non-Functional Design

### 4.1 Security
- **Data Encryption**: Employs Django encryption tools (e.g., `django-cryptography`) to encrypt static data.
- **Session Management**: Implement session timeout control via Redis, automatically logging out after 30 minutes of inactivity.
- **Permission Control**: Implement granular permission management based on Django's RBAC (Role-Based Access Control).

### 4.2 Performance
- **Data Synchronization**: Cache frequently accessed data (e.g., sessions, dashboard data) in Redis to reduce SQLite query load.
- **Response Time**: Optimized Django queries and leveraged indexes to enhance SQLite performance.

### 4.3 Compatibility
- **Browsers**: Supports latest versions of Chrome, Firefox, Safari, and Edge. Ensures interface compatibility using modern CSS (Flexbox, Grid).
- **IDE Integration**: Provides real-time coding support via VSCode Web API.

## 5. External Dependencies
- **Git**: Used for version control and branch management.
- **VSCode Web**: Supports real-time collaborative coding.
- **Authentication**: Integrates with external identity providers (e.g., OAuth2).
- **Document Storage**: Utilizes cloud storage services (e.g., AWS S3 or Django's file storage system) to store requirement documents.

## 6. System Workflow

### 6.1 Requirement Implementation Process
1. Product managers create requirements via the frontend interface, stored in SQLite.
2. Team leads assign tasks and create associated Git branches.
3. Developers implement code in VSCode Web and submit commits.
4. The lead verifies the code and resolves conflicts.
5. The product manager accepts the requirement and updates its status to “Closed.”

### 6.2 Conflict Resolution Process
1. The system detects Git merge conflicts and logs the affected files.
2. The frontend displays conflict warnings and invokes VSCode Web to open the files.
3. Developers manually resolve conflicts and submit updates.

## 7. Scalability Considerations
- **Redis Integration**: Redis can be enabled via configuration to optimize session management and data synchronization.
- **Modular Design**: Modules (e.g., requirement management, Git integration) are loosely coupled, supporting future addition of more extensions.


## 8. Risks and Assumptions
- **Risks**:
  - SQLite performance may be constrained in high-concurrency scenarios; consider migrating to PostgreSQL later.
  - Git integration may involve complex conflict resolution during intricate operations (e.g., rebase).
- **Assumptions**:
  - Users are familiar with basic Git operations.
  - External dependencies (e.g., authentication, cloud storage) remain stable.