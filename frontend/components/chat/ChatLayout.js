"use client";

export default function ChatLayout({
  sidebar,
  children,
}) {
  return (
    <section className="surface flex min-h-[70vh] overflow-hidden rounded-2xl">
      <aside className="hidden w-72 shrink-0 border-r border-white/[.07] bg-black/10 md:block">
        {sidebar}
      </aside>

      <main className="min-w-0 flex-1 overflow-hidden">
        {children}
      </main>
    </section>
  );
}