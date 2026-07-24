"use client";

import { useMemo, useState } from "react";
import { MessageSquarePlus, Search } from "lucide-react";

import { Button, EmptyState, LoadingCard } from "../ui";

export default function ConversationSidebar({
  conversations = [],
  activeId = null,
  loading = false,
  onNew,
  onSelect,
}) {
  // ==========================================================
  // Local State
  // ==========================================================

  const [searchTerm, setSearchTerm] = useState("");

  // ==========================================================
  // Search Filter
  // ==========================================================

  const filteredConversations = useMemo(() => {
    const query = searchTerm.trim().toLowerCase();

    if (!query) {
      return conversations;
    }

    return conversations.filter((conversation) =>
      (conversation?.title || "")
        .toLowerCase()
        .includes(query)
    );
  }, [conversations, searchTerm]);

  // ==========================================================
  // Group Conversations
  // ==========================================================

  const groupedConversations = useMemo(() => {
    const groups = {
      Today: [],
      Yesterday: [],
      "Last 7 Days": [],
      Older: [],
    };

    const today = new Date();

    filteredConversations.forEach((conversation) => {
      const date = new Date(
        conversation.updated_at ??
          conversation.created_at ??
          Date.now()
      );

      today.setHours(0, 0, 0, 0);
      date.setHours(0, 0, 0, 0);

      const diff = Math.floor(
  (today.getTime() - date.getTime()) /
    (1000 * 60 * 60 * 24)
      );
      if (diff === 0) {
        groups.Today.push(conversation);
      } else if (diff === 1) {
        groups.Yesterday.push(conversation);
      } else if (diff <= 7) {
        groups["Last 7 Days"].push(conversation);
      } else {
        groups.Older.push(conversation);
      }
    });

    return groups;
  }, [filteredConversations]);

  return (
    <div className="flex h-full flex-col p-3">

      <Button
        className="w-full"
        onClick={onNew}
      >
        <MessageSquarePlus className="h-4 w-4" />
        New conversation
      </Button>

      <div className="relative mt-4">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />

        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Search conversations..."
          className="w-full rounded-xl border border-white/10 bg-black/20 py-2 pl-10 pr-3 text-sm text-white outline-none ring-indigo-400/40 focus:ring-2"
        />
      </div>

      <p className="mt-6 mb-2 px-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
        Conversations
      </p>

      {/* ==========================================
          Conversation List
      ========================================== */}

      <div className="min-h-0 flex-1 space-y-2 overflow-y-auto">
        {loading ? (
          <LoadingCard label="Loading conversations" />
        ) : filteredConversations.length === 0 ? (
          <EmptyState
            title={
              searchTerm
                ? "No conversations found"
                : "No conversations"
            }
            copy={
              searchTerm
                ? "Try another search."
                : "Start a new chat to save it here."
            }
          />
        ) : (          Object.entries(groupedConversations).map(
            ([groupName, items]) => {
              if (items.length === 0) {
                return null;
              }

              return (
                <div key={groupName}>
                  <p className="mb-2 mt-5 px-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
                    {groupName}
                  </p>

                  <div className="space-y-1">
                    {items.map((conversation, index) => {
                      const id = conversation?.id ?? index;

                      const title =
                        conversation?.title?.trim() ||
                        "Untitled Conversation";

                      const date =
                        conversation?.updated_at ||
                        conversation?.created_at;

                      return (
                        <button
                          key={id}
                          type="button"
                          onClick={() => onSelect?.(id)}
                          className={`group w-full rounded-xl px-3 py-3 text-left transition-all duration-200 ${
                            id === activeId
                              ? "bg-indigo-500/15 text-indigo-100 ring-1 ring-indigo-400/20"
                              : "text-slate-400 hover:bg-white/[.05] hover:text-slate-100"
                          }`}
                        >
                          <div className="flex items-start justify-between gap-2">
                            <div className="min-w-0 flex-1">
                              <p className="truncate text-sm font-medium">
                                {title}
                              </p>

                              <p className="mt-1 text-xs text-slate-500">
                                {date
                                  ? new Date(date).toLocaleDateString()
                                  : "Just now"}
                              </p>
                            </div>

                            {/* Reserved for future actions */}
                            <div className="flex items-center opacity-0 transition-opacity group-hover:opacity-100">
                              <div className="h-2 w-2 rounded-full bg-slate-600" />
                            </div>
                          </div>
                        </button>
                      );
                    })}
                  </div>
                </div>
              );
            }
          )
        )}
      </div>
    </div>
  );
}