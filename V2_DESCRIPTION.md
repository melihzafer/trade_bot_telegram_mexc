@Workspace

We are expanding the core data model to support **Unit-Based Tracking** (e.g., "Price per Page", "Price per Article") alongside the existing Hourly and Fixed models.

Please execute the following schema migration and logic updates:

**1. Update Shared Types & Zod Schemas:**
* **File:** `src/shared/types.ts`
    * Update `PricingModel` type to include `'UNIT_BASED'`.
    * Update `Project` interface: Add optional `unitName` (string, e.g., "Page") and ensure `rate` represents "Price per Unit" when model is UNIT_BASED.
    * Update `Log` interface: Add optional `quantity` (number) for unit-based logs.
* **File:** `src/shared/schemas.ts`
    * Update `ProjectSchema` and `LogSchema` (Zod) to validate these new fields.

**2. Database Migration (Drizzle):**
* **File:** `drizzle/schema.ts`
    * Add `unit_name` (text) column to `projects` table.
    * Add `quantity` (real) column to `logs` table.
* **Action:** Generate a new migration file (`npm run drizzle:generate` command instruction is NOT needed, just provide the schema changes).

**3. Update Project Service:**
* **File:** `src/main/services/ProjectService.ts`
    * Ensure `create` and `update` methods handle the new fields properly.

**4. Update Frontend UI (Project Creation):**
* **File:** `src/renderer/src/components/CreateProjectForm.tsx`
    * Add a "Pricing Model" selector (Hourly / Fixed / Unit-Based).
    * If "Unit-Based" is selected, show an input for "Unit Name" (e.g., "Page", "Video").
    * Update the form submission logic to send `unitName` and `model`.

**5. Update Frontend UI (Timer/Logger):**
* **File:** `src/renderer/src/components/TimerWidget.tsx` (or a new `UnitCounter.tsx`)
    * Logic: If the active project is "Unit-Based", replace the timer (HH:MM:SS) with a **Counter** (+ / -) interface.
    * Feature: Show "Total Earnings" as `quantity * rate` in real-time.
    * Action: "Stop" button becomes "Log Units".

**Constraints:**
* Maintain existing functionality for Hourly projects.
* Use strict TypeScript types.
* Style new inputs with TailwindCSS (dark mode).