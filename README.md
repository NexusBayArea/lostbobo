# SimHPC Frontend

The SimHPC frontend is a modern React application built with TypeScript and Vite, styled with Tailwind CSS and shadcn/ui.

## Project Structure

- **`src/pages/`**: Contains all top-level page components (e.g., `Home.tsx`, `Dashboard.tsx`, `SignIn.tsx`).
- **`src/sections/`**: Reusable page sections (e.g., `Hero.tsx`, `Footer.tsx`).
- **`src/components/`**: Atomic UI components and common layouts.
- **`src/hooks/`**: Custom React hooks (e.g., `useAuth`, `useTheme`).
- **`src/lib/`**: External library configurations (e.g., `supabase.ts`, `utils.ts`).
- **`src/types/`**: TypeScript interfaces and types.

## Development

### Prerequisites
- Node.js 18+
- npm or yarn

### Setup
```bash
npm install
```

### Run Development Server
```bash
npm run dev
```

### Build for Production
```bash
npm run build
```

## Deployment
The frontend is automatically deployed to Vercel upon merging into the main branch of the `lostbobo` repository.
- **Primary**: https://simhpc.com
- **Backup**: https://nexusbayarea.github.io/lostbobo
