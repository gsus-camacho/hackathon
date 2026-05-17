# Implementation Plan: Planning System Consistency

## Issues Identified from Pitch Deck Analysis:

### 1. No Allergen Validation When Adding Products to Meal Plans ❌
- **Pilar 2 requirement**: "bloquea de raíz cualquier producto incompatible en el catálogo del estudiante"
- `add_item()` checks nothing against student's allergens/dietary profile

### 2. No WhatsApp Notification to Parent When Product Added ❌
- **Pilar 1 requirement**: "el padre recibe una alerta para bloquearlo o permitirlo con un clic"
- No notification sent when items are added to a child's plan

### 3. No Gemini Analysis Fallback ❌
- **Pilar 2 requirement**: "utilizamos la API de Gemini para analizar la composición inferida del nuevo ítem y cruzarla con el perfil del estudiante"
- No automatic defer-to-AI when parent doesn't respond

### 4. Generate Plan Doesn't Filter by Allergens ❌
- `generate_plan()` fetches top products without considering dietary restrictions

### 5. Reward Computation Overly Simplistic ❌
- Only monetary threshold check; no completeness criteria