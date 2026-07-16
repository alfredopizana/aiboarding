# SPEC-005 — 90-Day Success Plan

**Estado:** Aprobado · **Versión:** 1.0

## 1. Entrada

`UserProfile{name, role, team, start_date}` + plantillas de rol (`plans/templates.yaml`)
+ contexto RAG (docs del equipo) + people directory.

## 2. Modelo

```python
class PlanItem(BaseModel):
    title: str
    description: str
    category: Literal["learning","relationships","delivery","process"]
    suggested_contacts: list[str] = []   # person ids
    suggested_docs: list[str] = []       # uris
    done: bool = False

class PlanPhase(BaseModel):
    name: Literal["Days 1-30","Days 31-60","Days 61-90"]
    objective: str
    items: list[PlanItem]

class SuccessPlan(BaseModel):
    user: UserProfile
    generated_at: datetime
    phases: list[PlanPhase]   # exactamente 3
    summary: str
```

## 3. Reglas

1. Siempre 3 fases (30/60/90) con objetivo por fase:
   - 1-30: aprender y conectar (learning/relationships dominan).
   - 31-60: contribuir con apoyo (delivery empieza).
   - 61-90: entregar con autonomía y proponer mejoras.
2. Cada fase: 4–7 items, mezclando categorías.
3. Los items de `relationships` referencian personas reales del directorio
   (match por team/expertise); los de `learning` referencian docs reales ingeridos.
4. Plantilla base por rol en `templates.yaml` (`engineer`, `product`, `default`),
   enriquecida por LLM cuando provider ≠ fake.
5. Salidas: JSON (`SuccessPlan.model_dump()`) y Markdown renderizado.

## 4. Interfaces

- CLI: `aiboarding plan --name "Ana" --role engineer --team platform`
- API: `POST /plan` body `UserProfile` → `{plan, markdown}`
