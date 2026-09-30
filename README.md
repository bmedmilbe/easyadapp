# EasyAd — Marketplace API

EasyAd is a backend API for a marketplace platform, built with Django REST Framework and PostgreSQL.

The project focuses on reliable marketplace data management, API performance, automated testing and containerised deployment.

## 🚀 Key Features

* RESTful API built with Django REST Framework
* Marketplace data management
* PostgreSQL relational database
* Redis caching for frequently accessed data
* Versioned cache invalidation using Django signals
* Automated tests with pytest
* Media storage using AWS S3
* Docker-based development and deployment
* CI/CD with GitHub Actions
* Deployment through Railway

## 🏗️ Architecture

The application follows a Django REST architecture:

```text
Client
  |
  v
Django REST Framework
  |
  +---- PostgreSQL
  |
  +---- Redis
  |
  +---- AWS S3
```

Redis is used to reduce repeated database work for cached data. Django signals are used to keep cached data aligned with relevant updates.

## 🛠️ Technology Stack

| Technology            | Purpose             |
| --------------------- | ------------------- |
| Python                | Backend development |
| Django                | Web framework       |
| Django REST Framework | REST API            |
| PostgreSQL            | Relational database |
| Redis                 | Caching             |
| pytest                | Automated testing   |
| Docker                | Containerisation    |
| GitHub Actions        | CI/CD               |
| Railway               | Deployment          |
| AWS S3                | Media storage       |

## 🧪 Testing

The project uses `pytest` for automated testing.

Tests cover the main API and application behaviour and can be executed in the project environment using the configured pytest setup.

## 🚀 Getting Started

1. Clone the repository.
2. Install the project dependencies.
3. Configure the required environment variables.
4. Configure PostgreSQL and Redis.
5. Apply Django migrations.
6. Run the development server.
7. Run the test suite with pytest.

Refer to the project configuration files for the exact environment variables and commands.

## 📌 Engineering Focus

The project demonstrates practical backend development with a focus on:

* REST API design
* Database-backed application development
* Caching and cache invalidation
* Automated testing
* Containerisation
* CI/CD
* Cloud media storage
* Deployment

## 👨‍💻 Author

**Edmilbe Ramos**
Python Backend Developer

* GitHub: https://github.com/bmedmilbe
* LinkedIn: https://www.linkedin.com/in/edmilbe-ramos/
