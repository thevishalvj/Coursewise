import "dotenv/config";
import { defineConfig } from "prisma/config";

// The Prisma CLI (db push, migrate) uses DIRECT_URL, Supabase's session connection on
// port 5432. The running app uses DATABASE_URL, the pooled connection on port 6543.
export default defineConfig({
  schema: "prisma/schema.prisma",
  migrations: {
    path: "prisma/migrations",
  },
  datasource: {
    url: process.env["DIRECT_URL"] ?? process.env["DATABASE_URL"],
  },
});
