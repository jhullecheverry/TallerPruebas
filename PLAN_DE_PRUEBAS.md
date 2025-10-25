# Plan de Pruebas (TDD) — Sistema de Gestión de Proyectos y Tareas (Python)

Objetivo
Asegurar que las funcionalidades garantizan el comportamiento esperado y que las integraciones críticas funcionan correctamente. Empleo TDD: las pruebas describen el comportamiento y guían la implementación.

Alcance
- Pruebas unitarias e integración para:
  - Registro / Login (autenticación JWT)
  - Creación de proyectos, invitaciones y unión mediante token
  - Creación y movimiento de tareas (workflow)
  - Historial de tareas (audit trail)
  - Notificaciones persistentes y endpoint de streaming (SSE)
  - Reportes por proyecto

Estrategia
- Tests escritos con pytest + TestClient (FastAPI).
- Base de datos SQLite en memoria para cada test (aislamiento).
- Tests integrales que cubren los flujos: registro -> crear proyecto -> invitar -> unirse -> crear tarea -> mover tarea -> verificar historial y notificaciones.
- Ejecutar tests en cada commit / CI.

Tipos de pruebas
- Unitarias: funciones de `crud.py` que no dependen de FastAPI.
- Integración: endpoints HTTP con DB en memoria.
- Smoke tests: endpoints /health y endpoints principales.

Criterios de aceptación
- Todos los tests pasan localmente.
- Endpoints devuelven códigos HTTP correctos (201, 200, 401, 403, 404).
- Movimiento de tareas genera entradas en task_history.
- Invitaciones válidas permiten unirse a proyectos.
- Notificaciones se almacenan y pueden consultarse.

Cronograma simulado (Sprint de 2 semanas)
- Día 1: Setup del proyecto, entorno y estructura.
- Día 2-3: TDD Auth — tests de registro/login -> implementación.
- Día 4-5: TDD Projects — tests para crear proyecto, invitar, unirse -> implementación.
- Día 6-7: TDD Tasks — tests para creación/movimiento/historial -> implementación.
- Día 8: TDD Notifications — tests para almacenamiento y stream -> implementación.
- Día 9: Reportes -> tests e implementación.
- Día 10: Integración completa y corrección de bugs.
- Día 11-12: Documentación y limpieza.
- Día 13-14: Buffer / QA final.

Ejecución local de tests
1. pip install -r requirements.txt
2. pytest -q

Riesgos y mitigación
- Dependencias del sistema: usar versiones estables y SQLite (sin dependencias nativas).
- Interferencia entre tests: DB en memoria por test para aislamiento.
