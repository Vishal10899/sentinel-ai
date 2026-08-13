"use client";

import { useState, useRef, useEffect } from "react";
import { ChevronLeft, ChevronRight, Menu, X } from "lucide-react";

export default function ChatLayout({ sidebar, children, isFocusMode = false, onToggleFocusMode }) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [sidebarWidth, setSidebarWidth] = useState(280);
  const [isResizing, setIsResizing] = useState(false);
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  const startResizing = (e) => {
    e.preventDefault();
    setIsResizing(true);
  };

  useEffect(() => {
    const handleMouseMove = (e) => {
      if (!isResizing) return;
      const newWidth = e.clientX - 60; // offset sidebar
      if (newWidth >= 200 && newWidth <= 450) {
        setSidebarWidth(newWidth);
      }
    };

    const handleMouseUp = () => {
      setIsResizing(false);
    };

    if (isResizing) {
      window.addEventListener("mousemove", handleMouseMove);
      window.addEventListener("mouseup", handleMouseUp);
    }
    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
    };
  }, [isResizing]);

  const effectiveCollapsed = isCollapsed || isFocusMode;

  return (
    <section className="surface relative flex h-[calc(100vh-95px)] min-h-[600px] overflow-hidden rounded-2xl border border-white/10 bg-[#0d121f] transition-all">
      {/* Mobile Sidebar Toggle Button */}
      {!isFocusMode && (
        <button
          onClick={() => setIsMobileOpen(!isMobileOpen)}
          className="absolute left-3 top-3 z-40 rounded-lg border border-white/10 bg-black/40 p-2 text-slate-300 md:hidden hover:text-white"
          title="Toggle Menu"
        >
          {isMobileOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
        </button>
      )}

      {/* Desktop Resizable & Collapsible Sidebar */}
      {!isFocusMode && (
        <aside
          style={{ width: effectiveCollapsed ? 0 : `${sidebarWidth}px` }}
          className={`relative hidden shrink-0 border-r border-white/[.07] bg-black/20 md:block transition-all duration-200 ${
            effectiveCollapsed ? "overflow-hidden p-0 border-none" : ""
          }`}
        >
          {!effectiveCollapsed && sidebar}

          {/* Drag Handle */}
          {!effectiveCollapsed && (
            <div
              onMouseDown={startResizing}
              className="absolute right-0 top-0 bottom-0 w-1 cursor-col-resize hover:bg-indigo-500/50 transition-colors"
            />
          )}
        </aside>
      )}

      {/* Sidebar Collapse Toggle Button */}
      {!isFocusMode && (
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="hidden md:flex absolute top-3 z-30 items-center justify-center h-7 w-7 rounded-full border border-white/10 bg-[#121827] text-slate-400 hover:text-white transition shadow-lg cursor-pointer"
          style={{ left: effectiveCollapsed ? "12px" : `${sidebarWidth - 14}px` }}
          title={effectiveCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}
        >
          {effectiveCollapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </button>
      )}

      {/* Mobile Slide-Over Drawer */}
      {!isFocusMode && isMobileOpen && (
        <div className="fixed inset-0 z-50 flex md:hidden bg-black/70 backdrop-blur-sm">
          <div className="w-4/5 max-w-xs h-full bg-[#111827] border-r border-white/10 p-2">
            <div className="flex items-center justify-between p-2 border-b border-white/10 mb-2">
              <span className="text-xs font-bold text-white">Conversations</span>
              <button onClick={() => setIsMobileOpen(false)} className="p-1 text-slate-400">
                <X className="h-4 w-4" />
              </button>
            </div>
            {sidebar}
          </div>
        </div>
      )}

      {/* Main Chat Content Area */}
      <main className="min-w-0 flex-1 flex flex-col h-full overflow-hidden">{children}</main>
    </section>
  );
}