# Confluence — páginas de prueba (listas para pegar)

Crea estas 5 páginas en tu Space de Confluence. Para cada una: **New Page →**
pon el **título** de abajo → copia el **cuerpo** en el editor.

> 💡 Confluence entiende Markdown al pegar: en el editor teclea `/Markdown`
> (macro *Markdown*) o simplemente pega — títulos, listas y **negritas** se
> convierten. El conector de AIboarding lee el texto plano de la página, así
> que aunque el formato no quede perfecto, el contenido se ingiere igual.

---

## PÁGINA 1

**Título:** `New Hire FAQ`

**Cuerpo:**

Owner: People Ops (Ana Torres, @anat). Las preguntas que todo new hire hace en la primera semana — para que no tengas que dudar si está bien preguntar. (Siempre está bien preguntar.)

### Semana uno

**¿Cuándo llegan mis cuentas?** Todo (Google, Slack, Okta, GitHub) se aprovisiona antes del día uno — revisa el correo de bienvenida. ¿Falta algo? #it-helpdesk, se resuelve el mismo medio día según el IT Runbook.

**¿Quién es mi onboarding buddy?** Aparece en tu correo de bienvenida y en tu plan de 90 días. Los buddies son el canal de "ninguna pregunta es demasiado pequeña"; se ofrecieron para exactamente eso.

**¿Qué debo hacer en la semana uno?** Tu plan de 90 días lo lista, pero el resumen honesto: configura tu entorno, conoce a la gente de tu plan, entrega algo pequeño y lee el runbook de tu equipo. Nadie espera output en la semana uno; esperamos preguntas.

### Trabajando aquí

**¿Cuáles son las core hours?** No hay — somos async-first en 10 zonas horarias. Tu equipo puede tener una ventana de sync (pregunta a tu manager). Las juntas se agrupan 14:00–17:00 UTC; los updates escritos del viernes son el único ritmo obligatorio. Ver Communication Practices.

**¿Cómo tomo tiempo libre?** Solicítalo en el portal de RRHH, avisa a tu canal de equipo, listo. Sin teatro de aprobaciones para solicitudes razonables.

**¿Cuándo es el pago?** Último día hábil del mes, nómina local. Dudas → #people-ops.

### Ingeniería

**¿Cuándo puedo hacer deploy a producción?** En cuanto tu PR haga merge — `main` auto-despliega a staging y toma el siguiente release train. Tu buddy te acompaña en el primero.

**¿Cuándo entro a on-call?** Después de 90 días, primero haciendo shadowing — nunca en frío. Ver Incident Management.

**Creo que rompí algo.** Dilo de inmediato en el canal del equipo — la velocidad de la honestidad es todo el juego, y blameless es política, no un póster.

---

## PÁGINA 2

**Título:** `Mission, Vision & Values`

**Cuerpo:**

Owner: Leadership. Se revisa cada año en el offsite de enero; última revisión enero 2026.

### Misión

Ayudar a cada equipo a convertir su conocimiento disperso en respuestas que la gente realmente pueda usar.

### Visión

Un lugar de trabajo donde nadie pierde su primer mes buscando el documento, el owner o el acrónimo — donde el conocimiento de la empresa trabaja tan duro como su gente.

### Valores

Son herramientas de decisión, no pósters. Cuando dos valores chocan, di cuál estás sacrificando y por qué.

**1. Customers before comfort** — Hacemos lo incómodo cuando es lo correcto para el cliente. La conveniencia interna nunca supera la confianza del cliente.

**2. Show your work** — Las decisiones vienen con su razonamiento. Escribe donde otros lo encuentren; discrepa en abierto; cita tus fuentes.

**3. Small steps, shipped** — El momentum le gana a la magnitud. Entregamos la rebanada delgada, aprendemos y volvemos a entregar.

**4. Kind candor** — Decimos la verdad, y la decimos como quien planea seguir trabajando juntos. El feedback va a la persona, no sobre ella.

**5. Own the outcome** — "No es mi trabajo" no existe; "Voy a averiguar quién es el owner" sí. Cuando algo se rompe, arreglamos el sistema que lo permitió (postmortems blameless).

---

## PÁGINA 3

**Título:** `Org Chart & Teams`

**Cuerpo:**

Owner: People Ops (Ana Torres, @anat). Actualizado en cada cambio de equipo; fuente de verdad para preguntas de "qué equipo hace X".

### Organigrama

- CEO
  - CTO
    - Platform — James Lee · María Gómez
    - Website — Leo Martins · Hana Kim
    - DevOps — Lucas Almeida · Nina Petrova
    - Data — Priya Nair · Tomáš Novák
    - QA — Ken Watanabe · Elena Duarte
    - Security — Dev Patel · Yara Haddad
    - Custom Engineering — Grace Okafor · Mateo Rossi
  - Head of Product
    - Product — Sofía Ruiz
  - Head of Operations
    - People Ops — Ana Torres
    - IT — Raj Singh · Claire Dubois

> (Opcional: si quieres el diagrama visual, usa la macro **Mermaid** de Confluence con un `flowchart TD`.)

### Charters de equipo (una línea)

- **platform** — servicios core (auth, core-api, billing, notifications), arquitectura, backbone de on-call. #platform
- **web** — sitio de marketing + frontend de la web app, design system, performance, accesibilidad. #web
- **devops** — CI/CD, Kubernetes, Terraform, observabilidad, deploys y rollbacks. #devops
- **data** — warehouse, pipelines, dashboards, event tracking, experimentación. #data-eng
- **qa** — estrategia de pruebas, suite e2e, release sign-off, triage de bugs. #qa
- **security** — respuesta a incidentes, control de acceso, gestión de vulnerabilidades, compliance. #security
- **custom-eng** — integraciones de cliente y servicios profesionales sobre las APIs públicas. #custom-eng
- **product** — roadmap, discovery, specs, seguimiento de outcomes. #product
- **people** — hiring, onboarding, beneficios, marcos de crecimiento. #people-ops
- **it** — cuentas, laptops, administración de SaaS, helpdesk. #it-helpdesk

### ¿Qué equipo es dueño de mi pregunta?

- "Mi laptop/cuenta/VPN…" → IT (#it-helpdesk)
- "Deploy/pipeline/alerta…" → DevOps (#devops)
- "¿Esto es tema de seguridad?" → sí hasta que Security diga lo contrario (#security-incidents)
- "Los números del dashboard se ven mal" → Data (#data-eng)
- "Un cliente quiere una integración custom" → Custom Engineering (#custom-eng)
- "¿Por qué el producto hace X?" → Product (#product)
- "Beneficios/nómina/tiempo libre" → People Ops (#people-ops)

---

## PÁGINA 4

**Título:** `Communication Practices`

**Cuerpo:**

Owner: Operations (Ana Torres, @anat). Aplica a Slack, email, docs y juntas. Default: async-first, escrito y público — abarcamos 10 zonas horarias a propósito.

### Elegir el canal

- **Canal público de Slack** — default para todo. Si es de trabajo, va en un canal.
- **DM de Slack** — solo logística y temas personales. Las decisiones tomadas en DM se re-publican al canal.
- **Email** — partes externas, temas de RRHH/legal, cualquier cosa contractual.
- **Doc (Notion/spec)** — cualquier cosa con vida útil > 1 semana o audiencia > 1 equipo.
- **Junta** — temas de alto ancho de banda: conflicto, ambigüedad, brainstorming, 1:1s. No status.
- **Canal de incidente** — cualquier cosa urgente con impacto al cliente. La urgencia nunca viaja por DM.

### Etiqueta async

- **Sin mensajes de solo "hola".** Pon la pregunta en el primer mensaje, con contexto y qué necesitas.
- **Expectativas de respuesta**: canales 24 h, menciones directas el mismo día hábil, los DMs no son pagers.
- **Threads** mantienen los canales legibles; devuelve la conclusión al canal con un "TL;DR".
- **Los status updates son escritos**, en el canal del equipo, antes del viernes EOD — tres líneas: done / next / blocked.

### Escribir respetando al lector

1. Empieza con el ask o la respuesta; el contexto va abajo.
2. Un tema por mensaje o doc.
3. Fechas absolutas ("by Thu Jul 23, 18:00 UTC"), nunca "EOD" a través de 10 zonas horarias.
4. Nombra al decision-maker cuando abres una discusión (ver RACI).

### Idioma

El idioma de empresa es inglés para cualquier cosa cross-team; los canales en idioma local (#es-general, #pt-general) se fomentan para todo lo demás. Escribe para lectores no nativos: frases cortas, sin modismos.

---

## PÁGINA 5

**Título:** `Company Glossary`

**Cuerpo:**

Owner: todos (PRs bienvenidos — un término que tuviste que preguntar pertenece aquí). Orden alfabético.

**ADR** — Architecture Decision Record. Registro inmutable de una decisión técnica significativa. Superseded, nunca editado.

**Canary** — un deploy a producción enviado al 10% del tráfico por 15 minutos antes del rollout completo. Métricas en rojo durante el canary disparan auto-rollback. Ver DevOps Runbook.

**Error budget** — cuánta falta de fiabilidad permite el SLO (99.9% = ~43 min/mes). Cuando se gasta el budget, el trabajo de fiabilidad supera a las features.

**IC** — Incident Commander (durante incidentes). Ver Incident Management.

**Money paths** — los 12 user journeys cubiertos por la suite e2e (signup, checkout, invite…). "¿Toca un money path?" es una pregunta de riesgo de release.

**Postmortem** — el write-up blameless que se debe dentro de 5 días hábiles tras cualquier Sev1/Sev2.

**Release train** — la promoción staging→producción que sale martes y jueves 16:00 UTC. Si lo pierdes, tomas el siguiente — el tren no espera.

**RACI** — Responsible / Accountable / Consulted / Informed; la matriz de derechos de decisión. "¿Quién es la A en esto?" es la forma más rápida de destrabar una decisión.

**Sev1–Sev4** — escala de severidad de incidentes y bugs. Cuando dudes, elige la severidad más alta.

**SLO** — Service Level Objective, p.ej. 99.9% de disponibilidad mensual. Los SLOs alimentan los error budgets.

**Stop-the-line** — un build de `main` en rojo: prioridad #1 de todos hasta arreglarlo o revertirlo, presupuesto de 30 minutos.
