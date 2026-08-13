"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { 
  Shield, 
  ChevronDown, 
  ArrowRight, 
  Menu, 
  X, 
  Cpu, 
  Lock, 
  Zap, 
  BarChart3, 
  Terminal, 
  Building2 
} from "lucide-react";

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [activeDropdown, setActiveDropdown] = useState(null);

  useEffect(() => {
    const handleScroll = () => {
      if (window.scrollY > 20) {
        setScrolled(true);
      } else {
        setScrolled(false);
      }
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const navItems = [
    { 
      label: "Product", 
      href: "#architecture",
      dropdown: [
        { name: "Zero-Trust Proxy", desc: "Real-time payload inspection & PII sanitization", icon: Lock },
        { name: "Intelligent Routing", desc: "Dynamic model routing & latency fallback", icon: Cpu },
        { name: "Semantic Caching", desc: "Sub-millisecond query deduplication", icon: Zap },
        { name: "Observability & Tracing", desc: "Full audit logs & token economics", icon: BarChart3 }
      ]
    },
    { label: "Solutions", href: "#why-sentinel" },
    { label: "Enterprise", href: "#capabilities" },
    { label: "Developers", href: "#request-journey" },
    { label: "Resources", href: "#integrations" },
    { label: "Pricing", href: "#pricing" },
    { label: "Company", href: "#testimonials" },
  ];

  return (
    <header className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
      scrolled 
        ? "bg-[#07111F]/90 backdrop-blur-md border-b border-white/10 py-3.5 shadow-2xl" 
        : "bg-transparent py-5"
    }`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between">
          
          {/* Left: Brand Logo */}
          <Link href="/" className="flex items-center gap-3 group">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-blue-600 via-indigo-600 to-cyan-500 p-[1px] shadow-lg shadow-blue-500/20 group-hover:scale-105 transition-transform duration-200">
              <div className="w-full h-full bg-[#07111F] rounded-[7px] flex items-center justify-center">
                <Shield className="w-5 h-5 text-blue-400 group-hover:text-cyan-300 transition-colors" />
              </div>
            </div>
            <div className="flex flex-col">
              <span className="font-semibold text-lg tracking-tight text-white flex items-center gap-1.5 font-sans">
                Sentinel <span className="text-xs font-mono px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20 font-normal">AI</span>
              </span>
            </div>
          </Link>

          {/* Middle: Desktop Nav Links */}
          <nav className="hidden lg:flex items-center gap-1">
            {navItems.map((item) => (
              <div 
                key={item.label} 
                className="relative"
                onMouseEnter={() => item.dropdown && setActiveDropdown(item.label)}
                onMouseLeave={() => setActiveDropdown(null)}
              >
                <a
                  href={item.href}
                  className="px-3.5 py-2 text-xs font-medium text-slate-300 hover:text-white rounded-md hover:bg-white/5 transition-colors flex items-center gap-1"
                >
                  {item.label}
                  {item.dropdown && <ChevronDown className="w-3 h-3 text-slate-400" />}
                </a>

                {/* Dropdown Menu */}
                {item.dropdown && activeDropdown === item.label && (
                  <div className="absolute top-full left-0 mt-1 w-72 bg-[#0D1829] border border-white/10 rounded-xl shadow-2xl p-2 z-50 animate-in fade-in slide-in-from-top-2 duration-150">
                    {item.dropdown.map((subItem) => {
                      const Icon = subItem.icon;
                      return (
                        <a
                          key={subItem.name}
                          href={item.href}
                          className="flex items-start gap-3 p-2.5 rounded-lg hover:bg-white/5 transition-colors group/sub"
                        >
                          <div className="w-8 h-8 rounded-md bg-blue-500/10 border border-blue-500/20 flex items-center justify-center shrink-0 group-hover/sub:border-blue-400/40">
                            <Icon className="w-4 h-4 text-blue-400" />
                          </div>
                          <div>
                            <div className="text-xs font-semibold text-slate-100 group-hover/sub:text-blue-300">
                              {subItem.name}
                            </div>
                            <div className="text-[11px] text-slate-400 leading-snug mt-0.5">
                              {subItem.desc}
                            </div>
                          </div>
                        </a>
                      );
                    })}
                  </div>
                )}
              </div>
            ))}
          </nav>

          {/* Right: Actions */}
          <div className="hidden lg:flex items-center gap-3">
            <a
              href="#request-journey"
              className="px-3.5 py-2 text-xs font-medium text-slate-300 hover:text-white transition-colors"
            >
              Docs
            </a>
            <Link
              href="/login"
              className="px-3.5 py-2 text-xs font-medium text-slate-300 hover:text-white transition-colors"
            >
              Sign In
            </Link>
            <a
              href="#pricing"
              className="px-4 py-2 text-xs font-medium text-slate-200 border border-white/15 rounded-lg hover:bg-white/5 transition-all duration-200"
            >
              Book Demo
            </a>
            <a
              href="/register"
              className="px-4 py-2 text-xs font-medium text-white bg-blue-600 hover:bg-blue-500 rounded-lg shadow-lg shadow-blue-600/25 hover:shadow-blue-500/40 transition-all duration-200 flex items-center gap-1.5"
            >
              Start Free
              <ArrowRight className="w-3.5 h-3.5" />
            </a>
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="lg:hidden p-2 text-slate-300 hover:text-white focus:outline-none"
            aria-label="Toggle menu"
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>

        {/* Mobile Menu Panel */}
        {mobileMenuOpen && (
          <div className="lg:hidden mt-4 pt-4 border-t border-white/10 bg-[#07111F]/95 backdrop-blur-xl rounded-2xl p-5 space-y-4 animate-in fade-in duration-200">
            <div className="space-y-1">
              {navItems.map((item) => (
                <a
                  key={item.label}
                  href={item.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className="block px-3 py-2 text-sm font-medium text-slate-200 hover:text-white hover:bg-white/5 rounded-lg"
                >
                  {item.label}
                </a>
              ))}
            </div>
            <div className="pt-4 border-t border-white/10 flex flex-col gap-2.5">
              <Link
                href="/login"
                onClick={() => setMobileMenuOpen(false)}
                className="w-full text-center px-4 py-2.5 text-sm font-medium text-slate-200 border border-white/15 rounded-lg"
              >
                Sign In
              </Link>
              <a
                href="/register"
                onClick={() => setMobileMenuOpen(false)}
                className="w-full text-center px-4 py-2.5 text-sm font-medium text-white bg-blue-600 rounded-lg shadow-lg shadow-blue-600/30"
              >
                Start Free Trial
              </a>
            </div>
          </div>
        )}
      </div>
    </header>
  );
}
