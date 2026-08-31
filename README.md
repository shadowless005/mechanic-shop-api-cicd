# Mechanic Shop API

A RESTful API built with Flask for managing customers, mechanics, service tickets, and inventory for an automotive repair shop. The application includes JWT authentication, Swagger documentation, automated testing, CI/CD with GitHub Actions, and live deployment on Render.

## Features

### Customer Management

- Customer registration
- Customer login with JWT authentication
- View all customers
- View customer by ID
- Update customer information
- Delete customer account
- View authenticated customer's service tickets

### Mechanic Management

- Create mechanics
- View all mechanics
- Update mechanic information
- Delete mechanics
- View mechanics ranked by number of assigned service tickets

### Service Ticket Management

- Create service tickets
- View all service tickets
- Assign mechanics to service tickets
- Remove mechanics from service tickets
- Edit mechanic assignments
- Add inventory items to service tickets

### Inventory Management

- Create inventory items
- View all inventory items
- View inventory item by ID
- Update inventory items
- Delete inventory items

### Authentication & Security

- JWT Authentication
- Protected customer endpoints
- Password hashing
- Token-based authorization

### API Documentation

- Interactive Swagger UI documentation

### Automated Testing

- Customer endpoint tests
- Mechanic endpoint tests
- Service ticket endpoint tests
- Inventory endpoint tests
- Authentication tests
- Error handling tests

## Technologies Used

- Python
- Flask
- Flask SQLAlchemy
- SQLAlchemy
- Marshmallow
- MySQL
- PostgreSQL
- JWT Authentication
- Swagger UI
- unittest
- GitHub Actions
- Render

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
- GET `/mechanics/most-tickets`
- PUT `/mechanics/<id>`
- DELETE `/mechanics/<id>`

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

## Live API

**Render Deployment:**  
https://mechanic-shop-api-cicd.onrender.com

**Swagger Documentation:**  
https://mechanic-shop-api-cicd.onrender.com/api/docs/

## CI/CD

This project uses GitHub Actions to automatically:

- Install project dependencies
- Run all automated unit tests
- Deploy the application to Render after successful tests

## Project Highlights

- Full CRUD functionality
- JWT-secured authentication
- Swagger API documentation
- Comprehensive automated test suite
- GitHub Actions CI/CD pipeline
- Live deployment on Render
- RESTful API architecture
- Modular Flask Blueprint structure
- SQLAlchemy ORM with relational database design

## Repository

https://github.com/shadowless005/mechanic-shop-api-cicd

## Author

Matthew Shin

GitHub: https://github.com/shadowless005
