# Sistema de Gestión de Proyectos y Tareas (Python, TDD)

Resumen
Este proyecto es un backend implementado en Python (FastAPI) que ofrece un sistema de gestión de proyectos y tareas con las siguientes funcionalidades principales:

- Autenticación y autorización con JWT (registro / login, protección de rutas).
- Gestión de proyectos con miembros y sistema de invitaciones por token (invitar y unirse a proyectos).
- Gestión de tareas con flujo de trabajo (statuses) y historial de movimientos (audit trail).
- Canal de notificaciones (SSE) y feed de actividad almacenado.
- Reportes de avance por proyecto (conteo de tareas por estado).

Características extra
- TDD: tests automatizados con pytest y TestClient (tests incluidos).
- Base de datos: SQLite (archivo para ejecución local, in-memory para tests).
- Código modular y documentado.

Estructura principal
- main.py: entrypoint / creación de app
- db.py: inicialización de DB y modelos SQLAlchemy
- crud.py: operaciones de negocio (creación usuarios, proyectos, tareas...)
- auth.py: utilidades de autenticación y dependencias
- routes: en main.py se registran los endpoints
- tests/: suite de pruebas (pytest)

Requisitos
- Python 3.10+
- Instalar dependencias:
  pip install -r requirements.txt

Comandos
- Ejecutar tests:
  pytest -q
- Levantar servidor (dev):
  uvicorn main:app --reload --port 8000

Notas
- Para simplicidad el frontend no está incluido.
- Las invitaciones son tokens aleatorios guardados en DB con expiración.
- Las SSE son una implementación básica: los clientes se suscriben a /notifications/stream y reciben eventos en tiempo real.
