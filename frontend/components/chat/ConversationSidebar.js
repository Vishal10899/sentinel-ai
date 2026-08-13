"use client";

import { useEffect, useMemo, useState } from "react";
import { MessageSquarePlus, Search, Pin, Star, Archive, Trash2, Download, Edit2, Copy, Share2, RefreshCw, MoreVertical } from "lucide-react";
import { Button, EmptyState, LoadingCard } from "../ui";

export default function ConversationSidebar({
  conversations = [],
  activeId = null,
  loading = false,
  onNew,
  onSelect,
  onPin,
  onFavorite,
  onArchive,
  onDelete,
  onDuplicate,
  onShare,
  onRename,
  onExport,
  onRestore,
  onPermanentDelete,
}) {
  const [searchTerm, setSearchTerm] = useState("");
  const [menuOpenId, setMenuOpenId] = useState(null);
  const [showTrash, setShowTrash] = useState(false);

  // Global Keyboard Shortcuts (Ctrl+N: New Chat, Ctrl+/: Focus Search)
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "n") {
        e.preventDefault();
        onNew?.();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onNew]);

  const filteredConversations = useMemo(() => {
    const query = searchTerm.trim().toLowerCase();
    if (!query) return conversations;
    return conversations.filter((c) =>
      (c?.title || "").toLowerCase().includes(query)
    );
  }, [conversations, searchTerm]);

  const favoriteConversations = useMemo(
    () => filteredConversations.filter((c) => c.is_favorite && !c.is_deleted),
    [filteredConversations]
  );

  const pinnedConversations = useMemo(
    () => filteredConversations.filter((c) => c.is_pinned && !c.is_favorite && !c.is_deleted),
    [filteredConversations]
  );

  const regularConversations = useMemo(
    () => filteredConversations.filter((c) => !c.is_pinned && !c.is_favorite && !c.is_archived && !c.is_deleted),
    [filteredConversations]
  );

  const trashConversations = useMemo(
    () => filteredConversations.filter((c) => c.is_deleted),
    [filteredConversations]
  );

  return (
    <div className="flex h-full flex-col p-3 text-xs">
      <Button className="w-full" onClick={onNew}>
        <MessageSquarePlus className="h-4 w-4" /> New conversation
      </Button>

      <div className="relative mt-3">
        <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-500" />
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Search (Ctrl+/)"
          className="w-full rounded-xl border border-[var(--border-color)] bg-[var(--input-bg)] py-2 pl-9 pr-3 text-xs text-[var(--text-primary)] placeholder:text-[var(--text-muted)] outline-none focus:border-indigo-500/50 transition"
        />
      </div>

      <div className="flex items-center justify-between mt-3 px-1 text-[11px] text-slate-400">
        <span>History</span>
        <button
          onClick={() => setShowTrash(!showTrash)}
          className={`hover:text-white flex items-center gap-1 ${showTrash ? "text-rose-400 font-semibold" : ""}`}
        >
          <Trash2 className="h-3 w-3" /> {showTrash ? "Back to Chats" : `Trash (${trashConversations.length})`}
        </button>
      </div>

      <div className="min-h-0 flex-1 space-y-3 overflow-y-auto mt-2 pr-1">
        {loading ? (
          <LoadingCard label="Loading conversations..." />
        ) : showTrash ? (
          /* Trash / Soft-Deleted Section */
          <div>
            <p className="mb-2 px-2 text-[10px] font-bold uppercase tracking-wider text-rose-400">
              Soft Deleted Chats
            </p>
            {trashConversations.length === 0 ? (
              <p className="px-2 text-slate-500 text-[11px]">Trash is empty.</p>
            ) : (
              <div className="space-y-1">
                {trashConversations.map((c) => (
                  <div key={c.id} className="flex items-center justify-between rounded-xl bg-rose-500/10 px-3 py-2 text-rose-200">
                    <span className="truncate max-w-[140px]">{c.title}</span>
                    <div className="flex items-center gap-1">
                      <button onClick={() => onRestore?.(c.id)} className="p-1 hover:text-white" title="Restore">
                        <RefreshCw className="h-3 w-3 text-emerald-400" />
                      </button>
                      <button onClick={() => onPermanentDelete?.(c.id)} className="p-1 hover:text-rose-400" title="Delete permanently">
                        <Trash2 className="h-3 w-3 text-rose-400" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : filteredConversations.length === 0 ? (
          <EmptyState
            title={searchTerm ? "No conversations found" : "No active chats"}
            copy="Start a new conversation."
          />
        ) : (
          <>
            {/* Favorites Section */}
            {favoriteConversations.length > 0 && (
              <div>
                <p className="mb-1.5 px-2 text-[10px] font-bold uppercase tracking-wider text-amber-400 flex items-center gap-1">
                  <Star className="h-3 w-3 fill-amber-400 text-amber-400" /> Favorites
                </p>
                <div className="space-y-1">
                  {favoriteConversations.map((c) => (
                    <ConversationItem
                      key={c.id}
                      item={c}
                      activeId={activeId}
                      menuOpenId={menuOpenId}
                      setMenuOpenId={setMenuOpenId}
                      onSelect={onSelect}
                      onPin={onPin}
                      onFavorite={onFavorite}
                      onArchive={onArchive}
                      onDelete={onDelete}
                      onDuplicate={onDuplicate}
                      onShare={onShare}
                      onRename={onRename}
                      onExport={onExport}
                    />
                  ))}
                </div>
              </div>
            )}

            {/* Pinned Chats Section */}
            {pinnedConversations.length > 0 && (
              <div>
                <p className="mb-1.5 px-2 text-[10px] font-bold uppercase tracking-wider text-indigo-400 flex items-center gap-1">
                  <Pin className="h-3 w-3" /> Pinned
                </p>
                <div className="space-y-1">
                  {pinnedConversations.map((c) => (
                    <ConversationItem
                      key={c.id}
                      item={c}
                      activeId={activeId}
                      menuOpenId={menuOpenId}
                      setMenuOpenId={setMenuOpenId}
                      onSelect={onSelect}
                      onPin={onPin}
                      onFavorite={onFavorite}
                      onArchive={onArchive}
                      onDelete={onDelete}
                      onDuplicate={onDuplicate}
                      onShare={onShare}
                      onRename={onRename}
                      onExport={onExport}
                    />
                  ))}
                </div>
              </div>
            )}

            {/* Grouped Conversations by Date Buckets */}
            {(() => {
              const now = new Date();
              const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
              const yesterdayStart = todayStart - 86400000;
              const sevenDaysAgo = todayStart - 6 * 86400000;

              const groups = {
                today: [],
                yesterday: [],
                last7Days: [],
                older: [],
              };

              regularConversations.forEach((c) => {
                const time = new Date(c.updated_at || c.created_at || Date.now()).getTime();
                if (time >= todayStart) {
                  groups.today.push(c);
                } else if (time >= yesterdayStart) {
                  groups.yesterday.push(c);
                } else if (time >= sevenDaysAgo) {
                  groups.last7Days.push(c);
                } else {
                  groups.older.push(c);
                }
              });

              return (
                <div className="space-y-3">
                  {groups.today.length > 0 && (
                    <div>
                      <p className="mb-1.5 px-2 text-[10px] font-bold uppercase tracking-wider text-indigo-300">Today</p>
                      <div className="space-y-1">
                        {groups.today.map((c) => (
                          <ConversationItem key={c.id} item={c} activeId={activeId} menuOpenId={menuOpenId} setMenuOpenId={setMenuOpenId} onSelect={onSelect} onPin={onPin} onFavorite={onFavorite} onArchive={onArchive} onDelete={onDelete} onDuplicate={onDuplicate} onShare={onShare} onRename={onRename} onExport={onExport} />
                        ))}
                      </div>
                    </div>
                  )}

                  {groups.yesterday.length > 0 && (
                    <div>
                      <p className="mb-1.5 px-2 text-[10px] font-bold uppercase tracking-wider text-slate-400">Yesterday</p>
                      <div className="space-y-1">
                        {groups.yesterday.map((c) => (
                          <ConversationItem key={c.id} item={c} activeId={activeId} menuOpenId={menuOpenId} setMenuOpenId={setMenuOpenId} onSelect={onSelect} onPin={onPin} onFavorite={onFavorite} onArchive={onArchive} onDelete={onDelete} onDuplicate={onDuplicate} onShare={onShare} onRename={onRename} onExport={onExport} />
                        ))}
                      </div>
                    </div>
                  )}

                  {groups.last7Days.length > 0 && (
                    <div>
                      <p className="mb-1.5 px-2 text-[10px] font-bold uppercase tracking-wider text-slate-400">Last 7 Days</p>
                      <div className="space-y-1">
                        {groups.last7Days.map((c) => (
                          <ConversationItem key={c.id} item={c} activeId={activeId} menuOpenId={menuOpenId} setMenuOpenId={setMenuOpenId} onSelect={onSelect} onPin={onPin} onFavorite={onFavorite} onArchive={onArchive} onDelete={onDelete} onDuplicate={onDuplicate} onShare={onShare} onRename={onRename} onExport={onExport} />
                        ))}
                      </div>
                    </div>
                  )}

                  {groups.older.length > 0 && (
                    <div>
                      <p className="mb-1.5 px-2 text-[10px] font-bold uppercase tracking-wider text-slate-500">Older</p>
                      <div className="space-y-1">
                        {groups.older.map((c) => (
                          <ConversationItem key={c.id} item={c} activeId={activeId} menuOpenId={menuOpenId} setMenuOpenId={setMenuOpenId} onSelect={onSelect} onPin={onPin} onFavorite={onFavorite} onArchive={onArchive} onDelete={onDelete} onDuplicate={onDuplicate} onShare={onShare} onRename={onRename} onExport={onExport} />
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              );
            })()}
          </>
        )}
      </div>
    </div>
  );
}

function ConversationItem({
  item,
  activeId,
  menuOpenId,
  setMenuOpenId,
  onSelect,
  onPin,
  onFavorite,
  onArchive,
  onDelete,
  onDuplicate,
  onShare,
  onRename,
  onExport,
}) {
  const isMenuOpen = menuOpenId === item.id;

  return (
    <div
      onClick={() => onSelect?.(item.id)}
      className={`group relative flex items-center justify-between rounded-xl px-3 py-2.5 cursor-pointer transition ${
        item.id === activeId
          ? "bg-indigo-500/15 text-indigo-400 border border-indigo-500/30 font-semibold"
          : "text-[var(--text-secondary)] hover:bg-white/[0.04] hover:text-[var(--text-primary)]"
      }`}
    >
      <div className="min-w-0 flex-1 pr-2">
        <p className="truncate text-xs font-medium text-[var(--text-primary)]">{item.title || "Untitled Chat"}</p>
        <p className="text-[10px] text-[var(--text-muted)] mt-0.5">
          {item.updated_at ? new Date(item.updated_at).toLocaleDateString() : "Just now"}
        </p>
      </div>

      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
        <button
          onClick={(e) => {
            e.stopPropagation();
            onFavorite?.(item);
          }}
          className={`p-1 hover:text-amber-400 ${item.is_favorite ? "text-amber-400 opacity-100" : "text-[var(--text-muted)]"}`}
          title={item.is_favorite ? "Remove favorite" : "Mark favorite"}
        >
          <Star className={`h-3.5 w-3.5 ${item.is_favorite ? "fill-amber-400" : ""}`} />
        </button>

        <button
          onClick={(e) => {
            e.stopPropagation();
            onPin?.(item);
          }}
          className={`p-1 hover:text-indigo-400 ${item.is_pinned ? "text-indigo-400 opacity-100" : "text-[var(--text-muted)]"}`}
          title={item.is_pinned ? "Unpin chat" : "Pin chat"}
        >
          <Pin className="h-3.5 w-3.5" />
        </button>

        <button
          onClick={(e) => {
            e.stopPropagation();
            setMenuOpenId(isMenuOpen ? null : item.id);
          }}
          className="p-1 text-[var(--text-muted)] hover:text-[var(--text-primary)]"
        >
          <MoreVertical className="h-3.5 w-3.5" />
        </button>
      </div>

      {/* Contextual Dropdown Menu */}
      {isMenuOpen && (
        <div
          onClick={(e) => e.stopPropagation()}
          className="absolute right-2 top-8 z-30 w-40 rounded-xl border border-[var(--border-color)] bg-[var(--bg-elevated)] p-1 shadow-2xl text-[11px]"
        >
          <button
            onClick={() => {
              setMenuOpenId(null);
              const title = prompt("Rename conversation:", item.title);
              if (title && onRename) onRename(item.id, title);
            }}
            className="flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-[var(--text-secondary)] hover:bg-white/5 hover:text-[var(--text-primary)]"
          >
            <Edit2 className="h-3 w-3" /> Rename
          </button>
          <button
            onClick={() => {
              setMenuOpenId(null);
              onDuplicate?.(item.id);
            }}
            className="flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-slate-300 hover:bg-white/5 hover:text-white"
          >
            <Copy className="h-3 w-3" /> Duplicate
          </button>
          <button
            onClick={() => {
              setMenuOpenId(null);
              onShare?.(item.id);
            }}
            className="flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-slate-300 hover:bg-white/5 hover:text-white"
          >
            <Share2 className="h-3 w-3" /> Share Link
          </button>
          <button
            onClick={() => {
              setMenuOpenId(null);
              onExport?.(item);
            }}
            className="flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-slate-300 hover:bg-white/5 hover:text-white"
          >
            <Download className="h-3 w-3" /> Export JSON
          </button>
          <button
            onClick={() => {
              setMenuOpenId(null);
              onArchive?.(item);
            }}
            className="flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-slate-300 hover:bg-white/5 hover:text-white"
          >
            <Archive className="h-3 w-3" /> Archive
          </button>
          <button
            onClick={() => {
              setMenuOpenId(null);
              if (confirm("Move conversation to Trash?")) onDelete?.(item.id);
            }}
            className="flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-rose-400 hover:bg-rose-500/10"
          >
            <Trash2 className="h-3 w-3" /> Soft Delete
          </button>
        </div>
      )}
    </div>
  );
}