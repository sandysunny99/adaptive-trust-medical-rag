# Frontend Implementation Plan

## Technology Stack

| Layer | Technology | Justification |
|-------|------------|---------------|
| **Framework** | React 19 + TypeScript 5 | Type safety, ecosystem, component model |
| **Build** | Vite 6 | Fast dev server, HMR, proxy config |
| **Styling** | Tailwind CSS 4 | Utility-first, research-grade layouts |
| **Icons** | Lucide React | Clean, consistent iconography |
| **State** | React useState/useReducer | No external state library needed initially |
| **HTTP** | fetch + EventSource | Native APIs for REST + SSE |
| **Routing** | Page-based state | No router library needed for SPA |

## Project Structure

```
frontend/
├── index.html
├── package.json
├── vite.config.ts
├── tsconfig.json
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── index.css
│   ├── types/
│   │   └── index.ts           # Core type definitions
│   ├── components/
│   │   ├── Layout.tsx          # App shell + navigation
│   │   ├── MedicationCard.tsx  # Drug display card
│   │   ├── PipelineProgress.tsx # Real-time stage tracker
│   │   ├── ResultPanel.tsx     # Full analysis results
│   │   ├── TrustPanel.tsx      # Trust factor visualization
│   │   ├── EvidenceCard.tsx    # Evidence source display
│   │   ├── ClaimBadge.tsx      # Verification status badge
│   │   └── SecurityStatus.tsx  # Security gate indicators
│   ├── pages/
│   │   ├── WorkspacePage.tsx   # Main analysis page
│   │   ├── OverviewPage.tsx    # System overview
│   │   ├── EvidencePage.tsx    # Evidence explorer
│   │   ├── SecurityPage.tsx    # Security dashboard
│   │   ├── EvaluationPage.tsx  # Research evaluation
│   │   └── AuditPage.tsx       # Research audit trail
│   ├── hooks/
│   │   ├── useAnalysis.ts      # Analysis request + SSE
│   │   ├── useHealth.ts        # Backend health polling
│   │   └── usePipeline.ts      # Pipeline stage management
│   └── services/
│       ├── api.ts              # REST client
│       └── stream.ts           # SSE client
```

## Implementation Order

### Tier 1: Shell + Input (Current)
1. ✅ Vite + React + TypeScript scaffold
2. ✅ Tailwind CSS configuration
3. ✅ App shell with navigation
4. ✅ Drug input UI (direct entry)
5. ✅ Patient context form
6. ✅ Prescription image upload placeholder
7. ✅ Pipeline progress tracker
8. ✅ Result panel structure

### Tier 2: Backend Integration
9. REST client connecting to `/api/v1/analyze`
10. SSE client connecting to `/api/v1/stream/{id}`
11. Pipeline stage updates from real events
12. RxNorm medication cards from real normalization
13. Evidence cards from real retrieval

### Tier 3: Full Analysis Display
14. Drug-drug interaction results
15. Adverse reaction display
16. Warning / contraindication alerts
17. Food / administration guidance
18. Patient-specific considerations
19. Trust factor visualization (radar chart)
20. Claim verification details

### Tier 4: Advanced Features
21. Prescription image OCR flow
22. OCR confidence + correction UI
23. Evidence explorer page
24. Security dashboard page
25. Provenance chain visualization
26. Query history
27. Result export (PDF/JSON)

### Tier 5: Polish
28. Loading states + skeleton screens
29. Error handling + retry UI
30. Responsive design (mobile)
31. Accessibility (ARIA, keyboard nav)
32. Dark mode (optional)

## Dev Server Configuration

Frontend dev server: `http://localhost:5173`
Backend API server: `http://localhost:8000`

Vite proxy forwards `/api/*`, `/query`, `/health`, `/audit/*` to the backend.

## Non-Functional Requirements

- No PHI in frontend state or localStorage
- Research disclaimer visible on every page
- No auto-save of patient context
- No client-side medical logic
- All medical reasoning happens server-side
