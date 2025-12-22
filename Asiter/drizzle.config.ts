import type { Config } from "drizzle-kit";

export default {
  schema: "./src/lib/better-auth-schema.ts",
  out: "./drizzle",
  dialect: "sqlite",
  dbCredentials: {
    url: "./asiter-auth.db",
  },
} satisfies Config;

