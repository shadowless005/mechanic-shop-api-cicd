# Mechanic Shop API

A RESTful API built with Flask, SQLAlchemy, and Marshmallow for managing customers, mechanics, service tickets, and inventory in a mechanic shop. The project follows the Application Factory Pattern and demonstrates authentication, caching, rate limiting, pagination, and relational database management.

---

## Features

### Customer Management

- Customer CRUD operations
- Customer login with JWT authentication
- Protected customer routes
- View logged-in customer's service tickets

### Mechanic Management

- Mechanic CRUD operations
- Mechanics leaderboard (Most Tickets)

### Service Ticket Management

- Create service tickets
- View all service tickets
- Assign mechanics
- Remove mechanics
- Edit assigned mechanics
- Add inventory items to service tickets

### Inventory Management

- Inventory CRUD operations

### Additional Features

- JWT Authentication
- Protected Routes
- Rate Limiting
- Response Caching
- Pagination
- One-to-Many Relationships
- Many-to-Many Relationships

---

## Technologies Used

- Python
- Flask
- SQLAlchemy
- Marshmallow
- MySQL
- Flask-Limiter
- Flask-Caching
- Python-JOSE (JWT)
- Postman

---

## API Endpoints

### Customers

- POST `/customers/`
- GET `/customers/`
- GET `/customers/<id>`
- PUT `/customers/`
- DELETE `/customers/`
- POST `/customers/login`
- GET `/customers/my-tickets`

### Mechanics

- POST `/mechanics/`
- GET `/mechanics/`
- PUT `/mechanics/<id>`
- DELETE `/mechanics/<id>`
- GET `/mechanics/most-tickets`

### Service Tickets

- POST `/service-tickets/`
- GET `/service-tickets/`
- PUT `/service-tickets/<ticket_id>/assign-mechanic/<mechanic_id>`
- PUT `/service-tickets/<ticket_id>/remove-mechanic/<mechanic_id>`
- PUT `/service-tickets/<ticket_id>/edit`
- PUT `/service-tickets/<ticket_id>/add-inventory/<inventory_id>`

### Inventory

- POST `/inventory/`
- GET `/inventory/`
- GET `/inventory/<id>`
- PUT `/inventory/<id>`
- DELETE `/inventory/<id>`

---

## Author

Matthew Shin

Coding Temple Software Engineering Bootcamp
