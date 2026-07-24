"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ShieldCheck } from "lucide-react";
import { Button } from "./ui";
import api from "../lib/api";
import { useAuth } from "../providers/AuthProvider";

export function AuthCard({ mode }) {
  const router = useRouter();
  const { login } = useAuth();

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
  });

  const copy = {
  login: [
    "Welcome back",
    "Sign in to your Sentinel workspace.",
    "Sign In",
  ],

  register: [
    "Create your workspace",
    "Start routing with confidence.",
    "Create Account",
  ],

  forgot: [
    "Forgot Password",
    "Enter your email to receive a reset link.",
    "Send Reset Link",
  ],
}[mode];

  function update(e) {
    setForm({
      ...form,
      [e.target.name]: e.target.value,
    });
  }

  async function submit(e) {
    e.preventDefault();

    if (loading) return;
    if (mode === "register" && form.password.length < 8) {
      setError("Use a password with at least 8 characters.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      let response;

      if (mode === "login") {
        response = await api.login({
          email: form.email,
          password: form.password,
        });
      } else {
        response = await api.register({
          name: form.name,
          email: form.email,
          password: form.password,
        });
      }

      login(response);

      router.replace("/dashboard");
    } catch (err) {
      setError(err.message || "Authentication failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="grid min-h-screen place-items-center bg-[radial-gradient(circle_at_top,_rgba(99,102,241,.2),transparent_35rem)] p-5">
      <section className="surface w-full max-w-md p-8">

        <Link href="/" className="flex items-center gap-2 font-semibold">
          <span className="grid h-8 w-8 place-items-center rounded-lg bg-indigo-600">
            <ShieldCheck className="h-4 w-4" />
          </span>

          Sentinel AI
        </Link>

        <p className="eyebrow mt-8">
          Secure Workspace
        </p>

        <h1 className="mt-2 text-3xl font-bold">
          {copy[0]}
        </h1>

        <p className="mt-2 text-slate-400">
          {copy[1]}
        </p>

        <form
          onSubmit={submit}
          className="mt-8 space-y-5"
        >

          {mode === "register" && (
            <div>
              <label className="text-sm">
                Full Name
              </label>

              <input
                name="name"
                required
                value={form.name}
                onChange={update}
                className="mt-2 w-full rounded-xl border border-white/10 bg-black/20 p-3"
              />
            </div>
          )}

          <div>
            <label className="text-sm">
              Email
            </label>

            <input
              type="email"
              name="email"
              required
              value={form.email}
              onChange={update}
              className="mt-2 w-full rounded-xl border border-white/10 bg-black/20 p-3"
            />
          </div>

          <div>
            <label className="text-sm">
              Password
            </label>

            <input
              type="password"
              name="password"
              required
              value={form.password}
              onChange={update}
              className="mt-2 w-full rounded-xl border border-white/10 bg-black/20 p-3"
            />
          </div>

          {error && (
            <div className="rounded-lg bg-red-500/10 border border-red-500/20 p-3 text-sm text-red-300">
              {error}
            </div>
          )}

          <Button
            className="w-full"
            disabled={loading}
            type="submit"
          >
            {loading ? "Please wait..." : copy[2]}
          </Button>

        </form>

        <p className="mt-6 text-center text-sm text-slate-400">

          {mode === "login" ? (
            <>
              Don't have an account?{" "}
              <Link
                href="/register"
                className="text-indigo-400"
              >
                Register
              </Link>
            </>
          ) : (
            <>
              Already have an account?{" "}
              <Link
                href="/login"
                className="text-indigo-400"
              >
                Login
              </Link>
            </>
          )}

        </p>

      </section>
    </main>
  );
}
