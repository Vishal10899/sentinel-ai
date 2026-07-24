"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { MessageSquarePlus } from "lucide-react";
import { AppShell, PageTitle } from "../../components/shell";
import { Button, ErrorCard, LoadingCard, Toast } from "../../components/ui";
import ChatLayout from "../../components/chat/ChatLayout";
import ChatWindow from "../../components/chat/ChatWindow";
import ConversationSidebar from "../../components/chat/ConversationSidebar";
import { api } from "../../lib/api";

const ACTIVE_CONVERSATION_KEY = "sentinel:active-conversation";

export default function Playground() {
  const [models, setModels] = useState(null); const [conversations, setConversations] = useState([]); const [activeId, setActiveId] = useState("");
  const [messages, setMessages] = useState([]); const [prompt, setPrompt] = useState(""); const [selection, setSelection] = useState("");
  const [loading, setLoading] = useState(false); const [loadingConversations, setLoadingConversations] = useState(true); const [error, setError] = useState(""); const [lastPrompt, setLastPrompt] = useState(""); const [toast, setToast] = useState("");
  const selected = useMemo(() => models?.find(item => `${item.provider_id}:${item.model_id}` === selection), [models, selection]);
  const refreshConversations = useCallback(async () => { setLoadingConversations(true); try { const list = await api.getConversations(); setConversations(list); const stored = window.localStorage.getItem(ACTIVE_CONVERSATION_KEY); if (stored && list.some(item => item.id === stored)) setActiveId(stored); } catch (err) { setError(err.message); } finally { setLoadingConversations(false); } }, []);
  useEffect(() => { (async () => { try { const list = await api.models(); setModels(list); if (list[0]) setSelection(`${list[0].provider_id}:${list[0].model_id}`); await refreshConversations(); } catch (err) { setError(err.message); } })(); }, [refreshConversations]);
  const selectConversation = id => { if (loading || id === activeId) return; setError(""); setActiveId(id); window.localStorage.setItem(ACTIVE_CONVERSATION_KEY, id); };
  useEffect(() => { if (!activeId) return; let mounted = true; api.getMessages(activeId).then(result => { if (mounted) setMessages(result.messages); }).catch(err => { if (mounted) setError(err.message); }); return () => { mounted = false; }; }, [activeId]);
  const newConversation = () => { if (loading) return; setActiveId(""); setMessages([]); setPrompt(""); window.localStorage.removeItem(ACTIVE_CONVERSATION_KEY); };
  const ensureConversation = async title => { if (activeId) return activeId; const created = await api.createConversation({ title: title.slice(0, 80) || "New Conversation" }); setConversations(current => [created, ...current]); setActiveId(created.id); window.localStorage.setItem(ACTIVE_CONVERSATION_KEY, created.id); return created.id; };
  const send = async (overridePrompt) => { const text = (overridePrompt ?? prompt).trim(); if (!text || loading || !selection) return; const [provider, model] = selection.split(":"); setError(""); setLastPrompt(text); setPrompt(""); setLoading(true); const optimistic = { role: "user", content: text, created_at: new Date().toISOString() }; setMessages(current => [...current, optimistic]); try { const conversationId = await ensureConversation(text); const result = await api.sendMessage({ conversation_id: conversationId, provider, model, prompt: text }); setMessages(current => [...current, { role: "assistant", content: result.response, provider: result.provider, model: result.model, latency_ms: result.latency_ms, created_at: result.created_at }]); } catch (err) { setMessages(current => current.filter(item => item !== optimistic)); setPrompt(text); setError(err.message); } finally { setLoading(false); } };
  const retry = () => { if (lastPrompt && !loading) send(lastPrompt); };
  const copy = async text => { try { await navigator.clipboard.writeText(text); setToast("Response copied"); } catch { setToast("Clipboard access was unavailable"); } };
  const sidebar = <ConversationSidebar conversations={conversations} activeId={activeId} loading={loadingConversations} onNew={newConversation} onSelect={selectConversation} />;
  return (
  <AppShell
    title="Playground"
    subtitle="Enterprise AI chat with live provider responses"
  >
    <PageTitle
      eyebrow="AI workspace"
      title="Talk to your selected model"
      copy="Messages and response metadata are returned directly by the backend."
      action={
        <Button
          variant="secondary"
          className="md:hidden"
          onClick={newConversation}
        >
          <MessageSquarePlus className="h-4 w-4" />
          New chat
        </Button>
      }
    />

    {error && (
      <div className="mb-5">
        <ErrorCard
          error={error}
          retry={lastPrompt ? retry : refreshConversations}
        />
      </div>
    )}

    {!models ? (
      <LoadingCard label="Loading available models" />
    ) : (
      <>
        <ChatLayout sidebar={sidebar}>
          <header className="flex flex-col gap-3 border-b border-white/[.07] p-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="font-medium">
                {selected?.display_name || "Select a model"}
              </p>

              <p className="mt-1 text-xs text-slate-500">
                {activeId
                  ? "Conversation saved"
                  : "A conversation is created when you send your first message."}
              </p>
            </div>

            <select
              aria-label="Model"
              value={selection}
              disabled={loading}
              onChange={(event) => setSelection(event.target.value)}
              className="rounded-lg border border-white/10 bg-[#101522] px-3 py-2 text-sm disabled:opacity-60"
            >
              {models.map((item) => (
                <option
                  key={`${item.provider_id}:${item.model_id}`}
                  value={`${item.provider_id}:${item.model_id}`}
                >
                  {item.provider_name} · {item.display_name}
                </option>
              ))}
            </select>
          </header>

          <ChatWindow
            messages={messages}
            prompt={prompt}
            onPromptChange={setPrompt}
            onSend={send}
            onCopy={copy}
            onRetry={retry}
            loading={loading}
            stopSupported={false}
          />
        </ChatLayout>

        <Toast
          message={toast}
          clear={() => setToast("")}
        />
      </>
    )}
  </AppShell>
);
}
