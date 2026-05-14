# Cinepolis Natal Frontend

Browser-based SPA foundation for the full-stack Cinepolis Natal platform.

This workspace intentionally contains placeholders only. Full cinema UI flows will be implemented in dedicated frontend issues.

## Stack

- Next.js
- App Router
- TypeScript
- Node.js test runner with `tsx`
- ESLint

## Routes

The scaffold defines the PRD page entrypoints:

| Route | Page |
| --- | --- |
| `/` | Home |
| `/movies/[movieId]` | Movie Detail |
| `/sessions/[sessionId]/seats` | Seat Selection |
| `/ticket-types` | Ticket Type Selection |
| `/checkout` | Checkout |
| `/confirmation` | Confirmation |
| `/my-tickets` | My Tickets |
| `/login` | Login |
| `/register` | Register |

## API Configuration

The API client boundary lives at [`src/api/client.ts`](./src/api/client.ts).

Set the backend base URL with:

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

For local setup:

```bash
cp .env.example .env.local
```

## Commands

```bash
npm install
npm run dev
npm run lint
npm run test
npm run build
```

The Next.js dev server runs on `http://localhost:3000`.

## Docker

From the repository root:

```bash
docker compose up frontend
```

The Compose service injects `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` so the browser can call the backend through the host-exposed API port.
