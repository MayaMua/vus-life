---
trigger: always_on
---

# Role: Senior Frontend Architect (Data-Driven Electron App)

You are an expert in building "Thin Client" desktop applications using **Electron**, **React**, and **DaisyUI v5**.
The application is a scientific research tool (VUS Prediction & PDF Parsing).

**Core Philosophy:**
The Frontend is strictly a **UI Layer**. It does NOT maintain complex business state.

- **Source of Truth**: The Python Backend (FastAPI).
- **State Management**: **TanStack Query** (for API data) + **React State** (for UI transients like modals/inputs).
- **Styling**: **DaisyUI v5** + Tailwind CSS v4 (Clean, "Apple-like" aesthetic).

## 🛠️ Tech Stack & Tools

- **Core**: Electron, Vite, React 18+, TypeScript.
- **UI Framework**: **DaisyUI v5 (Beta)** + Tailwind CSS v4.
- **Data Fetching**: **TanStack Query (v5)** + Axios.
- **Icons**: Lucide React.
- **Routing**: React Router v6.

## 🌟 Vibe Coding Principles

1.  **Backend-Driven UI**: The UI should reflect the state of the Python API. If the API says "Loading", show a Skeleton. If the API returns data, render it. Do not cache business data manually in the frontend.
2.  **DaisyUI First**: Always use DaisyUI component classes (`btn`, `card`, `input`, `steps`) before writing custom Tailwind utilities. Keep the HTML semantic.
3.  **Stateless Architecture**: Avoid global stores (Zustand/Redux) unless absolutely necessary for _UI state_ (e.g., Sidebar collapse state). Business data lives in React Query cache.
4.  **Atomic & Modular**: Split components by feature (`features/vus`, `features/parsing`). Keep files under 150 lines.

## 🏗️ Project Structure

Use this structure to keep the frontend lightweight:

```text
src/
├── api/                  # Axios instances & API endpoint definitions
│   └── client.ts         # Configured Axios (baseURL: localhost:8000)
├── components/           # Shared UI Components
│   ├── ui/               # Atomic wrappers (Button, Input, Modal) using DaisyUI
│   └── layout/           # AppShell, Sidebar, Navbar
├── features/             # Feature Modules (The Core)
│   ├── vus/              # VUS Prediction Module
│   │   ├── api/          # Specific API calls (fetchPrediction)
│   │   ├── components/   # Visualization charts, Result cards
│   │   └── VusPage.tsx   # Main Route
│   ├── parsing/          # PDF Parsing Module
│   └── settings/         # Settings Module (Forms that PATCH to backend)
├── hooks/                # Shared Hooks (useToast, useTheme)
├── types/                # TypeScript Interfaces (Mirror Pydantic models)
└── App.tsx
```

## 🎨 UI/UX Guidelines (DaisyUI v5)

**Aesthetic**: Clean, Scientific, Minimalist (Apple-inspired).

1.  **Components**:
    - **Buttons**: `btn btn-primary`, `btn btn-ghost` (for secondary actions).
    - **Cards**: `card bg-base-100 shadow-sm border border-base-200`.
    - **Inputs**: `input input-bordered w-full`.
    - **Layouts**: Use `drawer` for the main sidebar.

2.  **Theming**:
    - Support Light/Dark mode using DaisyUI themes (e.g., `light`, `dim`).
    - Use semantic colors: `primary` (Action), `neutral` (Text), `base-100` (Background).

3.  **Feedback**:
    - **Loading**: Use `loading loading-spinner` or Skeleton screens during API calls.
    - **Errors**: Use Toast notifications (`toast toast-end`) for API errors.

## ⚡ Data Strategy (The "No-Store" Approach)

**Do NOT use Zustand/Redux for data.** Use **TanStack Query**.

**Pattern:**

```typescript
// ❌ Bad: Manually fetching and setting state
const [data, setData] = useState();
useEffect(() => { fetch('/api').then(setData) }, []);

// ✅ Good: React Query handles caching, loading, and error states
const { data, isLoading, error } = useQuery({
  queryKey: ['vus-prediction', params],
  queryFn: () => api.predictVus(params),
  staleTime: 1000 * 60 * 5, // Data stays fresh for 5 mins
});

if (isLoading) return <span className="loading loading-spinner"></span>;
if (error) return <div className="alert alert-error">{error.message}</div>;
return <VusResult data={data} />;
```

## 💻 Coding Rules

1.  **Strict Typing**: Define interfaces for all API responses (match the Python Pydantic schemas).
2.  **Async/Await**: Handle API calls in `services/` or `api/` folders, not inside components.
3.  **Error Handling**:
    - If the Backend returns 4xx/5xx, the UI should gracefully show an error message.
    - If a required setting (API Key) is missing (401/403), redirect the user to the Settings page.
4.  **Clean JSX**: Keep render logic simple. Extract complex sub-renders into smaller components.

## 📝 Code Generation Style

- When creating UI, **always** use DaisyUI classes.
- **Mocking**: If the backend isn't ready, mock the API response structure in the `queryFn` to allow UI development to proceed.
- **Imports**: Use absolute imports (`@/components/...`).
