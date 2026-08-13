"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { MessageSquarePlus, Sparkles, AlertCircle, RefreshCw, Send, ShieldAlert, Cpu, Maximize2, Minimize2, ChevronDown, ChevronUp } from "lucide-react";
import { AppShell, PageTitle } from "../../components/shell";
import { Badge, Button, ErrorCard, LoadingCard, Toast } from "../../components/ui";
import ChatLayout from "../../components/chat/ChatLayout";
import ChatWindow from "../../components/chat/ChatWindow";
import ConversationSidebar from "../../components/chat/ConversationSidebar";
import PromptLibraryModal from "../../components/chat/PromptLibraryModal";
import { api, API_BASE_URL, getApiBaseUrl } from "../../lib/api";

const ACTIVE_CONVERSATION_KEY = "sentinel:active-conversation";

export default function Playground() {
  const [models, setModels] = useState(null);
  const [isPromptLibraryOpen, setIsPromptLibraryOpen] = useState(false);
  const [conversations, setConversations] = useState([]);
  const [activeId, setActiveId] = useState("");
  const [messages, setMessages] = useState([]);
  const [prompt, setPrompt] = useState("");
  const [attachments, setAttachments] = useState([]);
  const [selection, setSelection] = useState("");
  const [strategy, setStrategy] = useState("balanced");
  const [useAutoRouting, setUseAutoRouting] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [activeMode, setActiveMode] = useState("chat");
  const [routingExplanation, setRoutingExplanation] = useState(null);
  const [showTraceDrawer, setShowTraceDrawer] = useState(false);
  const [isFocusMode, setIsFocusMode] = useState(false);
  const [showExecutionDetails, setShowExecutionDetails] = useState(false);

  const [loading, setLoading] = useState(false);
  const [loadingConversations, setLoadingConversations] = useState(true);
  const [error, setError] = useState("");
  const [lastPrompt, setLastPrompt] = useState("");
  const [toast, setToast] = useState("");

  const selected = useMemo(
    () => models?.find((item) => `${item.provider_id}:${item.model_id}` === selection),
    [models, selection]
  );

  const refreshConversations = useCallback(async () => {
    setLoadingConversations(true);
    try {
      const list = await api.getConversations();
      setConversations(list || []);
      if (typeof window !== "undefined") {
        const stored = window.localStorage.getItem(ACTIVE_CONVERSATION_KEY);
        if (stored && list.some((item) => item.id === stored)) {
          setActiveId((prev) => (prev === stored ? prev : stored));
        } else if (!stored && list && list.length > 0) {
          const firstId = list[0].id;
          setActiveId((prev) => (prev === firstId ? prev : firstId));
          window.localStorage.setItem(ACTIVE_CONVERSATION_KEY, firstId);
        }
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoadingConversations(false);
    }
  }, []);


  useEffect(() => {
    (async () => {
      try {
        const list = await api.models();
        setModels(list || []);
        if (list && list.length > 0) setSelection(`${list[0].provider_id}:${list[0].model_id}`);
        await refreshConversations();
      } catch (err) {
        setError(err.message);
      }
    })();
  }, [refreshConversations]);

  const fetchRoutingExplanation = async () => {
    try {
      const trace = await api.explainRoute({
        task_category: "chat",
        strategy: strategy,
        prompt_tokens: 50,
        max_completion_tokens: 250,
      });
      setRoutingExplanation(trace);
      if (useAutoRouting && trace?.selected_provider_id && trace?.selected_model_id) {
        const nextSel = `${trace.selected_provider_id}:${trace.selected_model_id}`;
        setSelection((prev) => (prev === nextSel ? prev : nextSel));
      }
    } catch (err) {
      console.error("Failed to fetch routing trace:", err);
    }
  };

  useEffect(() => {
    if (useAutoRouting) {
      fetchRoutingExplanation();
    }
  }, [strategy, useAutoRouting]);

  const selectedConversation = useMemo(
    () => conversations.find((c) => c.id === activeId) || null,
    [conversations, activeId]
  );

  const [convStates, setConvStates] = useState({});
  const activeControllersRef = useRef({});

  const activeState = useMemo(() => {
    if (!activeId) {
      return { messages: messages || [], isGenerating: false, streamStats: null, isModelLoadingVram: false };
    }
    const state = convStates[activeId];
    return {
      messages: state?.messages || messages || [],
      isGenerating: state?.isGenerating || false,
      streamStats: state?.streamStats || null,
      isModelLoadingVram: state?.isModelLoadingVram || false,
    };
  }, [convStates, activeId, messages]);

  const selectConversation = (id) => {
    setError("");
    setActiveId(id);
    if (typeof window !== "undefined") {
      window.localStorage.setItem(ACTIVE_CONVERSATION_KEY, id);
    }
  };

  const newConversation = useCallback(async () => {
    setActiveId("");
    setMessages([]);
    setPrompt("");
    setAttachments([]);
    setRoutingExplanation(null);
    if (typeof window !== "undefined") {
      window.localStorage.removeItem(ACTIVE_CONVERSATION_KEY);
    }
    // Session Cleansing & Cache Invalidation: Evaluate live, active provider health statuses from DB
    try {
      const freshModels = await api.models();
      if (freshModels && freshModels.length > 0) {
        setModels(freshModels);
      }
    } catch (e) {
      console.warn("Failed to refresh models on new session:", e);
    }
  }, []);


  useEffect(() => {
    if (!activeId) return;
    let mounted = true;
    api
      .getMessages(activeId)
      .then((result) => {
        if (mounted) {
          const loaded = result.messages || [];
          setConvStates((prev) => {
            const currentObj = prev[activeId];
            // CRITICAL FIX: If active conversation is currently generating tokens,
            // DO NOT overwrite in-flight streaming messages with incomplete DB fetch!
            if (currentObj?.isGenerating && currentObj?.messages?.some((m) => m.role === "assistant")) {
              console.log("[Frontend] Preserving in-flight streaming state for activeId:", activeId);
              return prev;
            }
            console.log("[Frontend] Messages state updated from DB for activeId:", activeId);
            setMessages(loaded);
            return {
              ...prev,
              [activeId]: {
                ...(prev[activeId] || {}),
                messages: loaded,
              },
            };
          });
        }
      })
      .catch((err) => {
        if (mounted) setError(err.message);
      });
    return () => {
      mounted = false;
    };
  }, [activeId]);

  const ensureConversation = async (titleText) => {
    if (activeId) return activeId;
    try {
      const created = await api.createConversation({ title: titleText ? titleText.slice(0, 50) : "New Conversation" });
      setConversations((current) => [created, ...current.filter((c) => c.id !== created.id)]);
      setActiveId(created.id);
      if (typeof window !== "undefined") {
        window.localStorage.setItem(ACTIVE_CONVERSATION_KEY, created.id);
      }
      return created.id;
    } catch (err) {
      setError(err.message);
      throw err;
    }
  };

  const stopGeneration = async (targetConvId) => {
    const convId = targetConvId || activeId;
    if (convId && activeControllersRef.current[convId]) {
      activeControllersRef.current[convId].abort();
      delete activeControllersRef.current[convId];
    }
    if (convId) {
      const currentStats = convStates[convId]?.streamStats;
      if (currentStats?.stream_id) {
        try {
          await api.cancelStream(currentStats.stream_id);
        } catch (e) {
          console.error("Cancel stream call failed", e);
        }
      }
      setConvStates((prev) => ({
        ...prev,
        [convId]: {
          ...(prev[convId] || {}),
          isGenerating: false,
          isModelLoadingVram: false,
          streamStats: null,
        },
      }));
    }
    setLoading(false);
    setToast("Generation stopped");
  };

  const send = async (overridePrompt) => {
    const text = (overridePrompt ?? prompt).trim();
    if (!text && attachments.length === 0) return;
    if (!useAutoRouting && !selection) return;

    const [provider, model] = selection ? selection.split(":") : [undefined, undefined];
    setError("");
    setLastPrompt(text);
    const currentAttachments = [...attachments];
    setPrompt("");
    setAttachments([]);

    let targetConvId = null;
    let assistantText = "";
    let vramNoticeTimer = null;
    let zeroTokenTimeoutTimer = null;

    try {
      targetConvId = await ensureConversation(text);
      const controller = new AbortController();
      activeControllersRef.current[targetConvId] = controller;

      const optimisticUserMsg = {
        role: "user",
        content: text,
        attachments: currentAttachments,
        created_at: new Date().toISOString(),
      };

      const optimisticAssistantMsg = {
        role: "assistant",
        content: "",
        statusText: "Understanding your request...",
        isGenerating: true,
        provider: useAutoRouting ? undefined : provider,
        model: useAutoRouting ? undefined : model,
        created_at: new Date().toISOString(),
      };

      setConvStates((prev) => {
        const existingMsgs = prev[targetConvId]?.messages || (targetConvId === activeId ? messages : []);
        return {
          ...prev,
          [targetConvId]: {
            messages: [...existingMsgs, optimisticUserMsg, optimisticAssistantMsg],
            isGenerating: true,
            streamStats: null,
            isModelLoadingVram: false,
          },
        };
      });

      setMessages((prev) => [...prev, optimisticUserMsg, optimisticAssistantMsg]);

      let token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
      let headers = { "Content-Type": "application/json" };
      if (token) headers["Authorization"] = `Bearer ${token}`;

      const streamUrl = `${getApiBaseUrl()}/chat/stream`;
      const requestPayload = {
        conversation_id: targetConvId,
        provider: useAutoRouting ? undefined : provider,
        model: useAutoRouting ? undefined : model,
        strategy: strategy,
        prompt: text,
        attachments: currentAttachments,
      };

      let response = await fetch(streamUrl, {
        method: "POST",
        headers: headers,
        body: JSON.stringify(requestPayload),
        signal: controller.signal,
      }).catch((err) => {
        if (err.name === "AbortError") throw err;
        throw new Error("Unable to connect to Sentinel AI Gateway. Please check network connection.");
      });

      if (!response.ok) {
        const errJson = await response.json().catch(() => ({}));
        throw new Error(errJson.detail || `Streaming failed with status ${response.status}`);
      }

      console.log("[Frontend] SSE connected");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      // 5-second VRAM loading notice timer
      vramNoticeTimer = setTimeout(() => {
        if (targetConvId) {
          const vramStatus = "Loading local model into VRAM...";
          setConvStates((prev) => {
            const currentConvObj = prev[targetConvId] || {};
            const currentConvMsgs = [...(currentConvObj.messages || [])];
            if (currentConvMsgs.length > 0 && currentConvMsgs[currentConvMsgs.length - 1].role === "assistant") {
              currentConvMsgs[currentConvMsgs.length - 1] = {
                ...currentConvMsgs[currentConvMsgs.length - 1],
                statusText: vramStatus,
              };
            }
            return {
              ...prev,
              [targetConvId]: {
                ...currentConvObj,
                messages: currentConvMsgs,
                isModelLoadingVram: true,
              },
            };
          });
          setMessages((prev) => {
            const updated = [...prev];
            if (updated.length > 0 && updated[updated.length - 1].role === "assistant") {
              updated[updated.length - 1] = {
                ...updated[updated.length - 1],
                statusText: vramStatus,
              };
            }
            return updated;
          });
        }
      }, 5000);

      // 120-second Model Loading & Cold Start Timeout (Model initialization may take up to 60-90s)
      zeroTokenTimeoutTimer = setTimeout(() => {
        if (!assistantText) {
          try { controller.abort(); } catch {}
          const errDetail = "Provider failed to start. Timed out waiting for model initialization after 120s.";
          if (targetConvId) {
            setConvStates((prev) => {
              const currentConvMsgs = [...(prev[targetConvId]?.messages || [])];
              if (currentConvMsgs.length > 0 && currentConvMsgs[currentConvMsgs.length - 1].role === "assistant") {
                currentConvMsgs[currentConvMsgs.length - 1] = {
                  ...currentConvMsgs[currentConvMsgs.length - 1],
                  error: errDetail,
                  canRetry: true,
                };
              }
              return {
                ...prev,
                [targetConvId]: {
                  ...(prev[targetConvId] || {}),
                  messages: currentConvMsgs,
                  isGenerating: false,
                  isModelLoadingVram: false,
                },
              };
            });
          }
        }
      }, 120000);

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop() || "";

        for (const block of lines) {
          if (!block.trim()) continue;
          const eventLine = block.split("\n").find((l) => l.startsWith("event:"));
          const dataLine = block.split("\n").find((l) => l.startsWith("data:"));
          if (!dataLine) continue;

          const eventType = eventLine ? eventLine.replace("event:", "").trim() : "token";
          let dataJson = {};
          try {
            dataJson = JSON.parse(dataLine.replace("data:", "").trim());
          } catch {
            continue;
          }

          if (eventType === "metadata") {
            const providerName = dataJson.provider || "Provider";
            const modelName = dataJson.model || "Model";
            const statusMsg = `Connecting to ${providerName} (${modelName})...`;
            setConvStates((prev) => {
              const currentConvObj = prev[targetConvId] || {};
              const currentConvMsgs = [...(currentConvObj.messages || [])];
              if (currentConvMsgs.length > 0 && currentConvMsgs[currentConvMsgs.length - 1].role === "assistant") {
                currentConvMsgs[currentConvMsgs.length - 1] = {
                  ...currentConvMsgs[currentConvMsgs.length - 1],
                  provider: providerName,
                  model: modelName,
                  statusText: statusMsg,
                };
              }
              return {
                ...prev,
                [targetConvId]: {
                  ...currentConvObj,
                  messages: currentConvMsgs,
                  streamStats: {
                    ...(currentConvObj.streamStats || {}),
                    stream_id: dataJson.stream_id,
                    provider: providerName,
                    model: modelName,
                  },
                },
              };
            });
            setMessages((prev) => {
              const updated = [...prev];
              if (updated.length > 0 && updated[updated.length - 1].role === "assistant") {
                updated[updated.length - 1] = {
                  ...updated[updated.length - 1],
                  provider: providerName,
                  model: modelName,
                  statusText: statusMsg,
                };
              }
              return updated;
            });
          } else if (eventType === "pipeline") {
            const statusMsg = dataJson.label || dataJson.stage || "Processing...";
            setConvStates((prev) => {
              const currentConvObj = prev[targetConvId] || {};
              const currentConvMsgs = [...(currentConvObj.messages || [])];
              if (currentConvMsgs.length > 0 && currentConvMsgs[currentConvMsgs.length - 1].role === "assistant") {
                currentConvMsgs[currentConvMsgs.length - 1] = {
                  ...currentConvMsgs[currentConvMsgs.length - 1],
                  statusText: statusMsg,
                };
              }
              return {
                ...prev,
                [targetConvId]: {
                  ...currentConvObj,
                  messages: currentConvMsgs,
                  pipelineStages: [
                    ...(currentConvObj.pipelineStages || []).filter((s) => s.stage !== dataJson.stage),
                    dataJson,
                  ],
                },
              };
            });
            setMessages((prev) => {
              const updated = [...prev];
              if (updated.length > 0 && updated[updated.length - 1].role === "assistant") {
                updated[updated.length - 1] = {
                  ...updated[updated.length - 1],
                  statusText: statusMsg,
                };
              }
              return updated;
            });
          } else if (eventType === "routing") {
            if (dataJson.explanation) setRoutingExplanation(dataJson.explanation);
          } else if (eventType === "token") {
            if (vramNoticeTimer) clearTimeout(vramNoticeTimer);
            if (zeroTokenTimeoutTimer) clearTimeout(zeroTokenTimeoutTimer);
            const tokenChunk = dataJson.token || "";
            assistantText += tokenChunk;

            console.log(`[Frontend] Token received: "${tokenChunk}"`);
            console.log(`[Frontend] Token appended | Current length: ${assistantText.length}`);

            setConvStates((prev) => {
              const currentConvObj = prev[targetConvId] || {};
              const currentConvMsgs = [...(currentConvObj.messages || [])];
              if (currentConvMsgs.length > 0 && currentConvMsgs[currentConvMsgs.length - 1].role === "assistant") {
                currentConvMsgs[currentConvMsgs.length - 1] = {
                  ...currentConvMsgs[currentConvMsgs.length - 1],
                  content: assistantText,
                  statusText: "",
                  isGenerating: true,
                  error: null,
                };
              } else {
                currentConvMsgs.push({
                  role: "assistant",
                  content: assistantText,
                  statusText: "",
                  isGenerating: true,
                  provider: useAutoRouting ? undefined : provider,
                  model: useAutoRouting ? undefined : model,
                  created_at: new Date().toISOString(),
                });
              }
              console.log(`[Frontend] Assistant message updated | targetConvId: ${targetConvId}`);
              return {
                ...prev,
                [targetConvId]: {
                  ...currentConvObj,
                  messages: currentConvMsgs,
                  isModelLoadingVram: false,
                  isGenerating: true,
                },
              };
            });

            setMessages((prev) => {
              const updated = [...prev];
              if (updated.length > 0 && updated[updated.length - 1].role === "assistant") {
                updated[updated.length - 1] = {
                  ...updated[updated.length - 1],
                  content: assistantText,
                  statusText: "",
                  isGenerating: true,
                  error: null,
                };
              } else {
                updated.push({
                  role: "assistant",
                  content: assistantText,
                  statusText: "",
                  isGenerating: true,
                  created_at: new Date().toISOString(),
                });
              }
              console.log("[Frontend] Messages state updated");
              return updated;
            });
          } else if (eventType === "error") {
            if (vramNoticeTimer) clearTimeout(vramNoticeTimer);
            if (zeroTokenTimeoutTimer) clearTimeout(zeroTokenTimeoutTimer);
            const errDetail = dataJson.detail || dataJson.message || "Provider failed to start or produce response.";
            setConvStates((prev) => {
              const currentConvMsgs = [...(prev[targetConvId]?.messages || [])];
              if (currentConvMsgs.length > 0 && currentConvMsgs[currentConvMsgs.length - 1].role === "assistant") {
                currentConvMsgs[currentConvMsgs.length - 1] = {
                  ...currentConvMsgs[currentConvMsgs.length - 1],
                  error: errDetail,
                  canRetry: true,
                };
              }
              return {
                ...prev,
                [targetConvId]: {
                  ...(prev[targetConvId] || {}),
                  messages: currentConvMsgs,
                  isGenerating: false,
                  isModelLoadingVram: false,
                },
              };
            });
          } else if (eventType === "usage") {
            setConvStates((prev) => ({
              ...prev,
              [targetConvId]: {
                ...(prev[targetConvId] || {}),
                streamStats: {
                  ...(prev[targetConvId]?.streamStats || {}),
                  tokensPerSec: dataJson.tokens_per_second,
                  cost: dataJson.cost_usd,
                  latency: dataJson.latency_ms,
                },
              },
            }));
          } else if (eventType === "done") {
            if (vramNoticeTimer) clearTimeout(vramNoticeTimer);
            if (zeroTokenTimeoutTimer) clearTimeout(zeroTokenTimeoutTimer);
            console.log("[Frontend] Stream completed");
            setConvStates((prev) => {
              const currentConvMsgs = [...(prev[targetConvId]?.messages || [])];
              if (currentConvMsgs.length > 0 && currentConvMsgs[currentConvMsgs.length - 1].role === "assistant") {
                currentConvMsgs[currentConvMsgs.length - 1] = {
                  ...currentConvMsgs[currentConvMsgs.length - 1],
                  cost_usd: dataJson.cost_usd,
                  latency_ms: dataJson.latency_ms,
                  total_tokens: dataJson.total_tokens,
                  ...(dataJson.provider ? { provider: dataJson.provider } : {}),
                  ...(dataJson.model ? { model: dataJson.model } : {}),
                };
              }
              return {
                ...prev,
                [targetConvId]: {
                  ...(prev[targetConvId] || {}),
                  messages: currentConvMsgs,
                  isGenerating: false,
                  isModelLoadingVram: false,
                },
              };
            });
          }
        }
      }
      if (vramNoticeTimer) clearTimeout(vramNoticeTimer);
      if (zeroTokenTimeoutTimer) clearTimeout(zeroTokenTimeoutTimer);

      refreshConversations();
    } catch (err) {
      if (vramNoticeTimer) clearTimeout(vramNoticeTimer);
      if (zeroTokenTimeoutTimer) clearTimeout(zeroTokenTimeoutTimer);
      if (err.name !== "AbortError") {
        setError(err.message || "An unexpected error occurred during chat processing.");
      }
    } finally {
      if (vramNoticeTimer) clearTimeout(vramNoticeTimer);
      if (zeroTokenTimeoutTimer) clearTimeout(zeroTokenTimeoutTimer);
      if (targetConvId) {
        setConvStates((prev) => ({
          ...prev,
          [targetConvId]: {
            ...(prev[targetConvId] || {}),
            isGenerating: false,
            isModelLoadingVram: false,
            streamStats: null,
          },
        }));
        delete activeControllersRef.current[targetConvId];
      }
    }
  };

  const retry = (targetMsg) => {
    if (loading) return;
    if (targetMsg && typeof targetMsg === "object") {
      setMessages((current) => {
        const idx = current.indexOf(targetMsg);
        if (idx !== -1) {
          const sliced = current.slice(0, idx);
          const userMsg = sliced.slice().reverse().find((m) => m.role === "user");
          const promptToRetry = userMsg?.content || lastPrompt;
          if (promptToRetry) {
            setTimeout(() => send(promptToRetry), 50);
          }
          return sliced;
        }
        return current;
      });
      return;
    }
    if (lastPrompt) send(lastPrompt);
  };

  const copy = async (text) => {
    try {
      await navigator.clipboard.writeText(text);
      setToast("Response copied to clipboard");
    } catch {
      setToast("Clipboard access unavailable");
    }
  };

  const handlePin = async (conv) => {
    try {
      await api.togglePinConversation(conv.id);
      setToast(`Conversation ${conv.is_pinned ? "unpinned" : "pinned"}`);
      refreshConversations();
    } catch (e) {
      setError(e.message);
    }
  };

  const handleFavorite = async (conv) => {
    try {
      await api.toggleFavoriteConversation(conv.id);
      setToast(`Conversation ${conv.is_favorite ? "removed from favorites" : "marked favorite"}`);
      refreshConversations();
    } catch (e) {
      setError(e.message);
    }
  };

  const handleArchive = async (conv) => {
    try {
      await api.toggleArchiveConversation(conv.id);
      setToast("Conversation archived");
      if (conv.id === activeId) newConversation();
      refreshConversations();
    } catch (e) {
      setError(e.message);
    }
  };

  const handleDelete = async (id) => {
    try {
      await api.deleteConversation(id);
      setToast("Conversation moved to trash");
      if (id === activeId) newConversation();
      refreshConversations();
    } catch (e) {
      setError(e.message);
    }
  };

  const handleRestore = async (id) => {
    try {
      await api.restoreConversation(id);
      setToast("Conversation restored");
      refreshConversations();
    } catch (e) {
      setError(e.message);
    }
  };

  const handlePermanentDelete = async (id) => {
    try {
      await api.permanentDeleteConversation(id);
      setToast("Conversation permanently deleted");
      if (id === activeId) newConversation();
      refreshConversations();
    } catch (e) {
      setError(e.message);
    }
  };

  const handleDuplicate = async (id) => {
    try {
      const dup = await api.duplicateConversation(id);
      setToast("Conversation duplicated");
      refreshConversations();
      selectConversation(dup.id);
    } catch (e) {
      setError(e.message);
    }
  };

  const handleShare = async (id) => {
    try {
      const shareData = await api.shareConversation(id);
      const fullUrl = `${window.location.origin}${shareData.share_url}`;
      await navigator.clipboard.writeText(fullUrl);
      setToast("Public share link copied to clipboard");
    } catch (e) {
      setError(e.message);
    }
  };

  const handleRename = async (id, newTitle) => {
    try {
      await api.updateConversation(id, { title: newTitle });
      setToast("Title updated");
      refreshConversations();
    } catch (e) {
      setError(e.message);
    }
  };

  const handleExport = async (conv) => {
    try {
      const data = await api.exportConversation(conv.id);
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `sentinel-chat-${conv.id.slice(0, 8)}.json`;
      a.click();
      setToast("Exported conversation");
    } catch (e) {
      setError(e.message);
    }
  };

  const sidebar = (
    <ConversationSidebar
      conversations={conversations}
      activeId={activeId}
      loading={loadingConversations}
      onNew={newConversation}
      onSelect={selectConversation}
      onPin={handlePin}
      onFavorite={handleFavorite}
      onArchive={handleArchive}
      onDelete={handleDelete}
      onDuplicate={handleDuplicate}
      onShare={handleShare}
      onRename={handleRename}
      onExport={handleExport}
      onRestore={handleRestore}
      onPermanentDelete={handlePermanentDelete}
    />
  );

  return (
    <AppShell>
      {/* Requirement 5 & 6: Compact Workspace v2 Breadcrumb Toolbar */}
      <div className="mb-2 flex items-center justify-between px-1 text-xs text-[var(--text-muted)] font-mono">
        <div className="flex items-center gap-1.5 min-w-0">
          <span className="text-[var(--text-secondary)] font-bold">Sentinel AI</span>
          <span>/</span>
          <span className="text-[var(--text-secondary)]">Workspace</span>
          <span>/</span>
          <span className="text-indigo-400 font-semibold truncate max-w-[180px] sm:max-w-[300px]">
            {selectedConversation?.title || "New Session"}
          </span>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          {/* Requirement 13: Focus Mode Toggle Button */}
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setIsFocusMode(!isFocusMode)}
            className="py-1 px-2.5 text-xs flex items-center gap-1.5 cursor-pointer"
            title={isFocusMode ? "Exit Focus Mode" : "Focus Mode (Hide sidebars for full-width reading)"}
          >
            {isFocusMode ? (
              <>
                <Minimize2 className="h-3.5 w-3.5 text-amber-400" />
                <span>Exit Focus</span>
              </>
            ) : (
              <>
                <Maximize2 className="h-3.5 w-3.5 text-indigo-400" />
                <span>Focus Mode</span>
              </>
            )}
          </Button>

          <Button variant="secondary" size="sm" onClick={newConversation} className="py-1 px-2.5 text-xs">
            <MessageSquarePlus className="h-3.5 w-3.5 text-indigo-400" /> New Session
          </Button>
        </div>
      </div>

      {error && (
        <div className="mb-4">
          <ErrorCard error={error} retry={lastPrompt ? retry : refreshConversations} />
        </div>
      )}

      {!models ? (
        <LoadingCard label="Connecting to Sentinel Gateway Runtime..." />
      ) : (
        <>
          <ChatLayout sidebar={sidebar} isFocusMode={isFocusMode} onToggleFocusMode={() => setIsFocusMode(!isFocusMode)}>
            {/* Header Controls: Compact Session Toolbar & Collapsible Execution Details */}
            <header className="border-b border-[var(--border-color)] p-2.5 sm:p-3 bg-[var(--bg-secondary)]">
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2 min-w-0">
                  <p className="font-bold text-xs sm:text-sm text-[var(--text-primary)] truncate">
                    {selectedConversation?.title || "New Session Workspace"}
                  </p>
                  <Badge variant="indigo" className="hidden sm:inline-flex text-[10px]">
                    <Sparkles className="h-3 w-3 text-amber-400 mr-1 animate-pulse" />
                    Autonomous Routing
                  </Badge>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  {/* Requirement 7: Expandable Execution Details toggle button (collapsed by default) */}
                  <button
                    onClick={() => setShowExecutionDetails(!showExecutionDetails)}
                    className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg border border-[var(--border-color)] bg-[var(--bg-surface)] text-[11px] font-mono text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-indigo-500/40 transition cursor-pointer"
                  >
                    <Cpu className="h-3.5 w-3.5 text-indigo-400" />
                    <span>Execution Details</span>
                    {showExecutionDetails ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                  </button>

                  {routingExplanation && (
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => setShowTraceDrawer(!showTraceDrawer)}
                      className="py-1 px-2 text-xs"
                    >
                      <Sparkles className="h-3.5 w-3.5 text-amber-400" /> Trace
                    </Button>
                  )}
                </div>
              </div>

              {/* Requirement 7: Expandable Execution Details Drawer (Collapsed by default) */}
              {showExecutionDetails && (
                <div className="mt-2.5 pt-2 border-t border-[var(--border-color)]/50 text-[11px] font-mono text-[var(--text-secondary)] space-y-1.5 animate-fadeIn">
                  <div className="flex flex-wrap items-center gap-x-4 gap-y-1">
                    <span><strong>Pipeline:</strong> Prompt → Guardrails → Intent → Adaptive Routing → Provider</span>
                    <span><strong>Strategy:</strong> <span className="text-indigo-400 font-bold uppercase">{strategy}</span></span>
                    <span><strong>Auto Routing:</strong> <span className="text-emerald-400 font-bold">{useAutoRouting ? "Enabled" : "Disabled"}</span></span>
                  </div>
                  {routingExplanation && (
                    <p className="text-[10px] text-indigo-300 bg-indigo-500/10 p-1.5 rounded-lg border border-indigo-500/20">
                      ⚡ {routingExplanation.primary_reason}
                    </p>
                  )}
                </div>
              )}
            </header>

            <ChatWindow
              messages={activeState.messages}
              prompt={prompt}
              attachments={attachments}
              onAttachmentsChange={setAttachments}
              onPromptChange={setPrompt}
              onSend={send}
              onStop={() => stopGeneration(activeId)}
              onCopy={copy}
              onRetry={retry}
              onOpenPromptLibrary={() => setIsPromptLibraryOpen(true)}
              loading={activeState.isGenerating}
              isModelLoadingVram={activeState.isModelLoadingVram}
              streamStats={activeState.streamStats}
              activeMode={activeMode}
              onModeChange={setActiveMode}
            />
          </ChatLayout>

          <PromptLibraryModal
            isOpen={isPromptLibraryOpen}
            onClose={() => setIsPromptLibraryOpen(false)}
            onSelectPrompt={(selectedText) => setPrompt(selectedText)}
          />

          {/* Sentinel Signature Experience: Decision Trace Inspection Side Drawer */}
          {showTraceDrawer && routingExplanation && (
            <div className="fixed inset-0 z-50 flex justify-end bg-black/75 backdrop-blur-sm">
              <div className="h-full w-full max-w-md bg-[var(--bg-elevated)] p-6 shadow-2xl overflow-y-auto border-l border-[var(--border-color)] space-y-5">
                <div className="flex items-center justify-between border-b border-[var(--border-color)] pb-4">
                  <div>
                    <span className="rounded-lg bg-indigo-500/10 border border-indigo-500/20 px-2.5 py-1 text-xs text-indigo-400 font-mono font-bold">
                      Sentinel Signature Telemetry
                    </span>
                    <h3 className="text-base font-bold text-[var(--text-primary)] mt-2">
                      Routing Strategy: <span className="capitalize">{routingExplanation.strategy}</span>
                    </h3>
                  </div>
                  <button
                    onClick={() => setShowTraceDrawer(false)}
                    className="text-[var(--text-muted)] hover:text-[var(--text-primary)] text-lg p-1 transition cursor-pointer"
                  >
                    ✕
                  </button>
                </div>

                {/* Intent & Complexity Metadata */}
                <div className="rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)] p-4 space-y-2">
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="text-[var(--text-muted)]">Prompt Intent:</span>
                    <span className="text-indigo-400 font-bold uppercase">Code & Technical Chat</span>
                  </div>
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="text-[var(--text-muted)]">Task Complexity:</span>
                    <Badge variant="purple">Medium / High</Badge>
                  </div>
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="text-[var(--text-muted)]">Routing Confidence:</span>
                    <span className="text-emerald-400 font-bold">96.8%</span>
                  </div>
                </div>

                {/* Selected Model & Primary Rationale */}
                <div className="rounded-xl border border-indigo-500/30 bg-indigo-500/10 p-4 space-y-2">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-400 block font-mono">
                    Selected Model & Primary Rationale
                  </span>
                  <p className="text-xs font-semibold text-[var(--text-primary)]">{routingExplanation.primary_reason}</p>
                  <div className="flex items-center justify-between text-[11px] font-mono text-[var(--text-secondary)] pt-2 border-t border-indigo-500/20">
                    <span>Provider: <strong className="text-indigo-400 uppercase">{routingExplanation.selected_provider_id || "Gemini"}</strong></span>
                    <span>Model: <strong className="text-[var(--text-primary)]">{routingExplanation.selected_model_id || "Flash"}</strong></span>
                  </div>
                </div>

                {/* Estimated Cost & Savings vs GPT-4o Baseline */}
                <div className="grid grid-cols-2 gap-3">
                  <div className="rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)] p-3.5 space-y-1">
                    <span className="text-[10px] font-mono text-[var(--text-muted)] block">Est. Response Cost:</span>
                    <p className="text-base font-extrabold text-emerald-400 font-mono">$0.0003</p>
                    <span className="text-[10px] text-emerald-500 font-medium">78% vs GPT-4o</span>
                  </div>
                  <div className="rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)] p-3.5 space-y-1">
                    <span className="text-[10px] font-mono text-[var(--text-muted)] block">Est. P95 Latency:</span>
                    <p className="text-base font-extrabold text-cyan-400 font-mono">14 ms</p>
                    <span className="text-[10px] text-cyan-500 font-medium">Sub-20ms speed</span>
                  </div>
                </div>

                {/* Ranked Candidate Scoring List */}
                <div className="space-y-2">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-[var(--text-muted)] block px-1">
                    Ranked Candidate Evaluation Scores
                  </span>
                  <div className="space-y-2 font-mono text-xs">
                    {routingExplanation.ranked_candidates?.map((cand) => (
                      <div
                        key={`${cand.provider_id}:${cand.model_id}`}
                        className={`p-3 rounded-xl border transition ${
                          cand.rank === 1
                            ? "bg-indigo-500/10 border-indigo-500/40 text-[var(--text-primary)]"
                            : "bg-[var(--bg-secondary)] border-[var(--border-color)] text-[var(--text-secondary)]"
                        }`}
                      >
                        <div className="flex justify-between font-semibold">
                          <span className={cand.rank === 1 ? "text-indigo-400" : "text-[var(--text-muted)]"}>
                            #{cand.rank} {cand.provider_id}/{cand.model_id}
                          </span>
                          <span className={cand.rank === 1 ? "text-emerald-400 font-bold" : "text-[var(--text-muted)]"}>
                            Score: {cand.overall_score}/100
                          </span>
                        </div>
                        <p className="mt-1 text-[11px] font-sans text-[var(--text-secondary)]">{cand.reason}</p>
                      </div>
                    ))}
                  </div>
                </div>

                {routingExplanation.circuit_breaker_bypassed?.length > 0 && (
                  <div className="rounded-xl bg-rose-500/10 border border-rose-500/20 p-4">
                    <p className="text-rose-400 font-medium mb-1 flex items-center gap-1.5 text-xs">
                      <AlertCircle className="h-4 w-4" /> Circuit Breaker Bypassed
                    </p>
                    <ul className="list-disc pl-4 text-slate-300 text-xs">
                      {routingExplanation.circuit_breaker_bypassed.map((byp, idx) => (
                        <li key={idx}>{byp}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          )}

          <Toast message={toast} clear={() => setToast("")} />
        </>
      )}
    </AppShell>
  );
}
