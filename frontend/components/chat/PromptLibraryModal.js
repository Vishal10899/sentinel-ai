"use client";

import { useState } from "react";
import { BookOpen, Search, X, Sparkles, Code, FileText, ShieldCheck, Mail, Database } from "lucide-react";
import { Button } from "../ui";

const PROMPT_TEMPLATES = [
  {
    id: "code-review",
    category: "Engineering",
    icon: Code,
    title: "Comprehensive Code Review",
    prompt: "Please perform a detailed code review of the following code snippet. Focus on performance optimizations, memory usage, security vulnerabilities, edge cases, and compliance with clean code principles.",
  },
  {
    id: "doc-summarize",
    category: "Analysis",
    icon: FileText,
    title: "Executive Document Summary",
    prompt: "Summarize the attached document into key takeaways, core findings, actionable recommendations, and potential risks. Structure the summary with bullet points suitable for an executive briefing.",
  },
  {
    id: "security-audit",
    category: "Security",
    icon: ShieldCheck,
    title: "Security & Vulnerability Audit",
    prompt: "Analyze the provided input for potential security threats, OWASP Top 10 vulnerabilities, input validation flaws, XSS vectors, or unauthorized data access patterns.",
  },
  {
    id: "sql-optimizer",
    category: "Database",
    icon: Database,
    title: "SQL Query Optimization",
    prompt: "Analyze and optimize the following SQL query. Explain index usage, JOIN efficiency, execution plan bottlenecks, and provide a refactored high-performance version.",
  },
  {
    id: "email-draft",
    category: "Communication",
    icon: Mail,
    title: "Professional Stakeholder Email",
    prompt: "Draft a clear, professional, and concise email to project stakeholders summarizing recent progress, current milestones, key risks, and upcoming deadlines.",
  },
  {
    id: "architecture-design",
    category: "Engineering",
    icon: Sparkles,
    title: "System Architecture Proposal",
    prompt: "Design an enterprise-grade cloud architecture for high availability, fault tolerance, horizontal scaling, and sub-100ms API latency. Include component breakdown and data flow.",
  },
];

export default function PromptLibraryModal({ isOpen, onClose, onSelectPrompt }) {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("All");

  if (!isOpen) return null;

  const categories = ["All", "Engineering", "Analysis", "Security", "Database", "Communication"];

  const filteredPrompts = PROMPT_TEMPLATES.filter((template) => {
    const matchesCategory = selectedCategory === "All" || template.category === selectedCategory;
    const matchesSearch =
      template.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      template.prompt.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="w-full max-w-2xl rounded-2xl border border-white/10 bg-[#111827] shadow-2xl overflow-hidden flex flex-col max-h-[85vh]">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-white/10 px-5 py-4 bg-white/[0.02]">
          <div className="flex items-center gap-2 text-indigo-400">
            <BookOpen className="h-5 w-5" />
            <h2 className="text-base font-semibold text-white">Employee Prompt Library</h2>
          </div>
          <button onClick={onClose} className="p-1 text-slate-400 hover:text-white rounded-lg hover:bg-white/10">
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Search & Category Filter */}
        <div className="p-5 space-y-3 border-b border-white/10 bg-black/20">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search prompt templates..."
              className="w-full rounded-xl border border-white/10 bg-black/40 py-2.5 pl-10 pr-4 text-xs text-white outline-none focus:border-indigo-500/50"
            />
          </div>

          <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs">
            {categories.map((cat) => (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                className={`rounded-lg px-3 py-1.5 font-medium transition ${
                  selectedCategory === cat
                    ? "bg-indigo-600 text-white"
                    : "bg-white/5 text-slate-400 hover:bg-white/10 hover:text-white"
                }`}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>

        {/* Prompts Grid */}
        <div className="flex-1 overflow-y-auto p-5 space-y-3">
          {filteredPrompts.length === 0 ? (
            <p className="text-center text-slate-500 py-8 text-xs">No matching templates found.</p>
          ) : (
            filteredPrompts.map((template) => {
              const Icon = template.icon;
              return (
                <div
                  key={template.id}
                  onClick={() => {
                    onSelectPrompt(template.prompt);
                    onClose();
                  }}
                  className="group flex items-start gap-3 rounded-xl border border-white/10 bg-white/[0.03] p-4 cursor-pointer hover:border-indigo-500/50 hover:bg-indigo-500/10 transition"
                >
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-indigo-500/20 text-indigo-400 group-hover:scale-105 transition-transform">
                    <Icon className="h-5 w-5" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-between">
                      <h3 className="text-xs font-semibold text-white group-hover:text-indigo-300">{template.title}</h3>
                      <span className="text-[10px] uppercase font-bold text-slate-500">{template.category}</span>
                    </div>
                    <p className="mt-1 text-[11px] text-slate-400 line-clamp-2 leading-relaxed">{template.prompt}</p>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
