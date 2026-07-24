import Link from "next/link";

export default function ForgotPassword() {
  return (
    <main className="grid min-h-screen place-items-center">
      <div className="surface max-w-md rounded-xl p-8 text-center">
        <h1 className="text-2xl font-bold">Forgot Password</h1>

        <p className="mt-4 text-slate-400">
          Password reset functionality will be available in the next
          authentication update.
        </p>

        <Link
          href="/login"
          className="mt-6 inline-block text-indigo-400"
        >
          Back to Login
        </Link>
      </div>
    </main>
  );
}