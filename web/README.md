# Coursewise web app

Next.js chat app. It stores your chats in Supabase Postgres (through Prisma) and asks the
FastAPI service in `../ai` for answers. All calls to the AI service happen server-side.

## One-time setup

1. **Supabase keys.** In the Supabase dashboard, open *Project Settings > API* and copy the
   project URL and the publishable key.
2. **Database URLs.** Click *Connect* at the top of the dashboard, choose *ORMs > Prisma*, and
   copy the two connection strings (pooled on 6543, direct on 5432). Put in your database password.
3. **Email login.** In *Authentication > URL Configuration*, set *Site URL* to
   `http://localhost:3000` and add `http://localhost:3000/auth/callback` to *Redirect URLs*.
4. Create `web/.env.local` from the template and fill it in:

```bash
cp .env.example .env.local
```

5. Install and create the tables in Supabase:

```bash
npm install
```

```bash
npm run db:push
```

## Run

Start the AI service first (see the root README), then:

```bash
npm run dev
```

Open http://localhost:3000, enter your email, and click the link Supabase sends you.

## Layout

| Path | What it does |
|---|---|
| `prisma/schema.prisma` | User, Conversation, Message models |
| `src/proxy.ts` | Refreshes the Supabase session and redirects signed-out users to `/login` |
| `src/app/api/chat/route.ts` | Saves the question, calls FastAPI `/ask`, saves the answer |
| `src/app/api/conversations/` | List, load, and delete your conversations |
| `src/app/auth/callback/route.ts` | Finishes the email-link sign-in |
| `src/components/Chat.tsx` | The chat UI |
