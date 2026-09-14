# Finance Platform — Backend

Plataforma de finanzas personales con categorización automática de transacciones (reglas + fallback LLM),
aprendizaje continuo a partir de las correcciones del usuario, e insights en lenguaje natural generados
a partir de datos ya calculados por el backend.

## Por qué este proyecto

No es un tracker de gastos más. El diferenciador es que el sistema **entiende** las transacciones en vez
de solo registrarlas: las categoriza sin que el usuario etiquete nada, aprende de sus correcciones, y
redacta insights accionables ("tus gastos en Comida aumentaron 306.8% este mes") en vez de mostrar solo
números crudos.

La IA se usa con un propósito específico y explicable — categorización y redacción de insights — nunca
como un chatbot genérico ni como wrapper superficial de un LLM.

---

## Stack

| Capa | Tecnología |
|---|---|
| Backend | Django 6 + Django REST Framework |
| Auth | JWT (`djangorestframework-simplejwt`) |
| Base de datos | PostgreSQL (Neon en producción, contenedor local en desarrollo) |
| Tareas async | Celery + Redis (Upstash en producción) |
| LLM | Gemini API (`gemini-3.5-flash-lite`) — free tier |
| Import de datos | pandas |
| Infraestructura local | Docker Compose |
| Despliegue (planeado) | Render (free tier) |

---

## Arquitectura general

```
Cliente (React, pendiente)
        │ HTTPS + JWT
        ▼
Django REST Framework (API)
        │                    │
        ▼                    ▼
   PostgreSQL           Celery (async)
                              │
                              ▼
                         Redis (broker)
                              │
                              ▼
                    Gemini API (fallback LLM)
```

**Principio de diseño central:** todo lo que dependa de una API externa (LLM) o sea potencialmente lento
(parseo de CSV, categorización) corre en Celery, nunca bloquea el request HTTP. El usuario siempre recibe
respuesta inmediata; el procesamiento pesado pasa en segundo plano.

---

## Apps del proyecto (modularidad por dominio)

| App | Responsabilidad |
|---|---|
| `accounts` | Custom User model, autenticación |
| `finances` | `Account`, `Category`, `Transaction` — el core del dominio, + endpoint de resumen del dashboard |
| `budgets` | `Budget`, cálculo de progreso y alertas por categoría |
| `goals` | `SavingsGoal`, proyección de cumplimiento |
| `categorization` | Motor de categorización (reglas + fallback LLM + aprendizaje) |
| `insights` | Cálculo de cambios de gasto + redacción en lenguaje natural |
| `imports_` | Pipeline de carga de CSV bancario |

---

## El motor de categorización — la pieza central del proyecto

Diseño en tres capas, pensado para minimizar costo y latencia sin sacrificar cobertura:

```
Transacción nueva
      │
      ▼
Capa 1 — Reglas (CategoryRule)         instantáneo, gratis, determinístico
   coincide?  ──sí──▶ categorizada
      │no
      ▼
Capa 2 — Gemini (fallback LLM)         ~1-2s, gasta cuota, solo si Capa 1 falla
   coincide?  ──sí──▶ categorizada
      │no
      ▼
Queda "pending" para revisión manual
```

**Capa 1 — Reglas de palabras clave.** Un modelo `CategoryRule` (keyword → categoría) resuelve la mayoría
de las transacciones recurrentes (UBER, NETFLIX, SUPERMAXI, etc.) sin tocar ninguna API externa. Reglas
globales (compartidas) + reglas por usuario (personalizadas).

**Capa 2 — Fallback con Gemini.** Solo se invoca cuando ninguna regla coincide. Se le pasa al LLM la lista
exacta de categorías existentes del usuario (nunca se le permite "inventar" una categoría nueva), y se le
pide una respuesta JSON estructurada (`{"category": ..., "confidence": ...}`) para evitar parsear texto
libre. Cualquier fallo (rate limit, timeout, respuesta inesperada) se captura sin tumbar la tarea — la
transacción simplemente queda pendiente en vez de romper el sistema.

**Aprendizaje continuo.** Cuando el usuario corrige una transacción a mano (`PATCH`), o confirma
explícitamente que una categorización de la IA fue correcta (`POST /transactions/<id>/confirm/`), el
sistema extrae una palabra clave distintiva de la descripción y crea automáticamente una `CategoryRule`
personal. La próxima transacción similar se resuelve por regla, sin volver a gastar una llamada al LLM.
Esto significa que el sistema **reduce su propia dependencia del LLM con el uso** — verificado end-to-end:
una transacción sin regla pasó por Gemini, se confirmó, y la siguiente transacción similar ya se resolvió
en capa 1.

**Por qué las reglas aprendidas son por usuario y no globales:** los comercios recurrentes de un usuario
(su restaurante de barrio, su farmacia) no tienen significado para otros usuarios. Evita que una corrección
de una persona "contamine" las categorías de todos los demás.

---

## Insights en lenguaje natural

Regla de oro del diseño: **el LLM nunca calcula números, solo los redacta.**

```
Django calcula el cambio de gasto por categoría (agregaciones SQL puras)
                    │
                    ▼
Gemini redacta UNA frase natural a partir del número YA calculado
                    │
                    ▼
Se guarda el Insight con el texto + los datos exactos que lo respaldan (supporting_data)
```

Si Gemini falla, existe una plantilla de respaldo (`_fallback_text`) que genera el mismo insight con una
redacción fija — el usuario nunca se queda sin información por una falla del LLM, solo pierde algo de
naturalidad en el texto.

Solo se generan insights para cambios de gasto ≥15% mes contra mes, para evitar ruido sobre variaciones
insignificantes.

---

## Import de CSV

Flujo: `ImportJob` (tracking de estado) → tarea de Celery → `pandas` parsea el archivo con soporte de
nombres de columna flexibles (español/inglés) → `bulk_create` de las transacciones → categorización
individual de cada una vía Celery.

**Detalle técnico relevante:** `bulk_create` no dispara los signals de Django (por diseño, para no perder
la ventaja de velocidad de una inserción masiva). Por eso el pipeline dispara manualmente la
categorización de cada transacción creada, en vez de depender del signal automático que sí se usa para
transacciones creadas una por una vía API.

---

## Autenticación y aislamiento de datos

JWT vía `simplejwt`. Cada `ViewSet` filtra su `queryset` por `self.request.user` — no solo se valida que
el usuario esté autenticado, se garantiza que nunca pueda ver ni modificar datos de otro usuario, incluso
si adivina un ID en la URL.

---

## Decisiones de arquitectura para correr 100% gratis

| Necesidad | Solución free-tier | Trade-off aceptado |
|---|---|---|
| PostgreSQL en producción | Neon | — |
| Redis (broker de Celery) | Upstash | — |
| Hosting del backend | Render (free web service) | Se duerme tras inactividad (~30-50s de cold start) |
| Worker de Celery | Corre como subproceso dentro del mismo servicio web (`scripts/start-render.sh`) | No hay aislamiento de proceso real entre API y worker; en producción "de verdad" irían en servicios separados |
| LLM | Gemini API free tier | Límite diario de requests (holgado para este volumen) |

Estas decisiones están documentadas para poder explicarlas en entrevista como trade-offs conscientes,
no como limitaciones no consideradas.

---

## Modelos principales

```
User (custom)
  └── Account
        └── Transaction ── Category ── CategoryRule (por usuario o global)
              └── (categorization_method: rule | llm | manual | pending)

Budget (user, category, limit, period) → progreso calculado en vivo
SavingsGoal (user, target, current, target_date) → proyección calculada en vivo
Insight (user, texto generado, supporting_data)
ImportJob (user, account, file, status, total/processed rows)
```

---

## Endpoints principales

| Método | Endpoint | Qué hace |
|---|---|---|
| `POST` | `/api/token/` | Login, devuelve JWT access + refresh |
| `GET/POST` | `/api/accounts/` | CRUD de cuentas |
| `GET/POST` | `/api/categories/` | CRUD de categorías |
| `GET/POST/PATCH` | `/api/transactions/` | CRUD de transacciones |
| `POST` | `/api/transactions/<id>/confirm/` | Confirma categorización, dispara aprendizaje |
| `GET/POST` | `/api/imports/` | Sube un CSV, dispara procesamiento async |
| `GET/POST` | `/api/budgets/` | CRUD de presupuestos, con progreso calculado |
| `GET/POST` | `/api/goals/` | CRUD de metas, con proyección calculada |
| `GET` | `/api/insights/` | Lista insights generados |
| `POST` | `/api/insights/generate/` | Genera insights nuevos a partir de los datos actuales |
| `GET` | `/api/dashboard/summary/` | Payload agregado para el dashboard (gasto por categoría, tendencia mensual, balance) |

---

## Levantar en local

```bash
cp .env.example .env
# Completa SECRET_KEY y GEMINI_API_KEY

docker compose up --build -d
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```

API disponible en `http://localhost:8000/api/`, admin en `http://localhost:8000/admin/`.

---

## Limitaciones conocidas (documentadas, no accidentales)

- **Proyección de metas de ahorro:** asume una tasa de ahorro constante desde la creación de la meta,
  calculada sobre `current_amount / días transcurridos`. Una versión más precisa analizaría el historial
  real de depósitos. Aceptable para v1, identificado como siguiente iteración.
- **Aprendizaje de reglas:** la extracción de palabra clave usa la palabra más larga de la descripción
  (excluyendo una lista de stopwords) — funciona bien para nombres de comercios distintivos, pero es una
  heurística simple, no NLP real.
- **Encoding:** algunas categorías sembradas por migración tuvieron problemas de codificación de acentos
  (corregido manualmente); los emojis de `icon` están planeados para reemplazarse por nombres de íconos de
  `lucide-react` en el frontend, en vez de arreglarse en el backend.

---

## Estado del proyecto

- [x] Infraestructura (Docker, Postgres, Redis, Celery)
- [x] Auth JWT + custom User + aislamiento de datos por usuario
- [x] Modelos core + API REST completa
- [x] Motor de categorización de 3 capas (reglas → LLM → aprendizaje), verificado end-to-end
- [x] Import de CSV en bulk con categorización automática
- [x] Budgets y Goals con cálculos en vivo
- [x] Insights en lenguaje natural
- [x] Endpoint de resumen para el dashboard
- [ ] Frontend en React
- [ ] Despliegue (Neon + Upstash + Render)