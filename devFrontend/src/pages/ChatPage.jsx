import { useEffect, useMemo, useState } from "react";

const STORAGE_KEYS = {
  apiUrl: "langapp_api_url",
  token: "langapp_token",
};

function formatDate(value) {
  if (!value) return "";
  try {
    return new Date(value).toLocaleString();
  } catch {
    return value;
  }
}

function normalizeApiUrl(url) {
  return (url || "").trim().replace(/\/+$/, "");
}

function decodeJwtPayload(token) {
  try {
    const raw = (token || "").replace(/^Bearer\s+/i, "").trim();
    const parts = raw.split(".");

    if (parts.length < 2) return null;

    const base64Url = parts[1];
    const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
    const padded = base64 + "=".repeat((4 - (base64.length % 4)) % 4);
    const json = atob(padded);
    return JSON.parse(json);
  } catch {
    return null;
  }
}

async function apiFetch({ apiUrl, token, path, method = "GET", body }) {
  const res = await fetch(`${normalizeApiUrl(apiUrl)}${path}`, {
    method,
    headers: {
      Authorization: token,
      "Content-Type": "application/json",
    },
    body: body ? JSON.stringify(body) : undefined,
  });

  const text = await res.text();
  let data = null;

  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = text;
  }

  if (!res.ok) {
    throw new Error(
      typeof data === "string"
        ? data
        : JSON.stringify(data || { status: res.status }, null, 2)
    );
  }

  return data;
}

export default function ChatPage() {
  const [apiUrl, setApiUrl] = useState(
    localStorage.getItem(STORAGE_KEYS.apiUrl)
  );
  const [token, setToken] = useState(
    localStorage.getItem(STORAGE_KEYS.token)
  );

  const [conversations, setConversations] = useState([]);
  const [selectedConversationId, setSelectedConversationId] = useState("");
  const [selectedConversation, setSelectedConversation] = useState(null);

  const [newConversationTitle, setNewConversationTitle] = useState("Test convo");
  const [newPersonaId, setNewPersonaId] = useState("italian-tutor");
  const [messageInput, setMessageInput] = useState("");

  const [loadingConversations, setLoadingConversations] = useState(false);
  const [loadingConversation, setLoadingConversation] = useState(false);
  const [sendingMessage, setSendingMessage] = useState(false);
  const [creatingConversation, setCreatingConversation] = useState(false);

  const [error, setError] = useState("");
  const [lastUsage, setLastUsage] = useState(null);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEYS.apiUrl, apiUrl);
  }, [apiUrl]);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEYS.token, token);
  }, [token]);

  const canCallApi = useMemo(() => {
    return normalizeApiUrl(apiUrl) && token.trim();
  }, [apiUrl, token]);

  const decodedToken = useMemo(() => decodeJwtPayload(token), [token]);

  const debugUser = useMemo(() => {
    if (!decodedToken) return null;

    return {
      name: decodedToken.name || decodedToken.display_name || "",
      userId: decodedToken.user_id || decodedToken.sub || "",
      email: decodedToken.email || "",
    };
  }, [decodedToken]);

  function refreshCredentials() {
    const latestApiUrl = localStorage.getItem(STORAGE_KEYS.apiUrl) || apiUrl;
    const latestToken = localStorage.getItem(STORAGE_KEYS.token) || "";

    setApiUrl(latestApiUrl);
    setToken(latestToken);
  }

  async function loadConversations() {
    if (!canCallApi) return;
    setError("");
    setLoadingConversations(true);
    try {
      const data = await apiFetch({
        apiUrl,
        token,
        path: "/conversations",
      });

      const items = Array.isArray(data) ? data : data.items || [];
      setConversations(items);

      if (!selectedConversationId && items.length > 0) {
        setSelectedConversationId(items[0].conversationId || items[0].id || "");
      }
    } catch (err) {
      setError(`Failed to load conversations: ${err.message}`);
    } finally {
      setLoadingConversations(false);
    }
  }

  async function loadConversation(conversationId) {
    if (!conversationId) return;
    setError("");
    setLoadingConversation(true);
    try {
      const data = await apiFetch({
        apiUrl,
        token,
        path: `/conversations/${conversationId}`,
      });
      setSelectedConversation(data);
    } catch (err) {
      setError(`Failed to load conversation: ${err.message}`);
    } finally {
      setLoadingConversation(false);
    }
  }

  async function createConversation() {
    if (!canCallApi) return;
    setError("");
    setCreatingConversation(true);
    try {
      const data = await apiFetch({
        apiUrl,
        token,
        path: "/conversations",
        method: "POST",
        body: {
          personaId: newPersonaId.trim(),
          title: newConversationTitle.trim(),
        },
      });

      const createdId = data.conversationId || data.id;
      await loadConversations();

      if (createdId) {
        setSelectedConversationId(createdId);
        await loadConversation(createdId);
      }
    } catch (err) {
      setError(`Failed to create conversation: ${err.message}`);
    } finally {
      setCreatingConversation(false);
    }
  }

  async function sendMessage() {
    if (!selectedConversationId || !messageInput.trim()) return;
    setError("");
    setSendingMessage(true);

    try {
      const data = await apiFetch({
        apiUrl,
        token,
        path: `/conversations/${selectedConversationId}/messages`,
        method: "POST",
        body: {
          content: messageInput.trim(),
        },
      });

      setLastUsage(data.usage || null);
      setMessageInput("");

      await loadConversation(selectedConversationId);
      await loadConversations();
    } catch (err) {
      setError(`Failed to send message: ${err.message}`);
    } finally {
      setSendingMessage(false);
    }
  }

  useEffect(() => {
    loadConversations();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (selectedConversationId) {
      loadConversation(selectedConversationId);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedConversationId]);

  const messages = [...(selectedConversation?.messages || [])].sort(
    (a, b) => new Date(a.createdAt) - new Date(b.createdAt)
  );

  return (
    <div style={styles.app}>
      <div style={styles.sidebar}>
        <h2 style={styles.h2}>Language App Tester</h2>

        <label style={styles.label}>API URL</label>
        <input
          style={styles.input}
          value={apiUrl}
          onChange={(e) => setApiUrl(e.target.value)}
          placeholder="https://your-api.execute-api.eu-central-1.amazonaws.com"
        />

        <label style={styles.label}>Authorization Token</label>
        <textarea
          style={{ ...styles.textarea, minHeight: 90 }}
          value={token}
          onChange={(e) => setToken(e.target.value)}
          placeholder="Bearer ..."
        />

        <button
          style={styles.button}
          onClick={refreshCredentials}
        >
          Refresh Credentials
        </button>

        {debugUser && (
          <div style={styles.debugCard}>
            <div style={styles.debugTitle}>Decoded token</div>
            <div><strong>Name:</strong> {debugUser.name || "—"}</div>
            <div><strong>User ID:</strong> {debugUser.userId || "—"}</div>
            <div><strong>Email:</strong> {debugUser.email || "—"}</div>
          </div>
        )}

        <button
          style={styles.button}
          onClick={loadConversations}
          disabled={!canCallApi || loadingConversations}
        >
          {loadingConversations ? "Loading..." : "Refresh Conversations"}
        </button>

        <div style={styles.section}>
          <h3 style={styles.h3}>Create Conversation</h3>

          <label style={styles.label}>Persona ID</label>
          <input
            style={styles.input}
            value={newPersonaId}
            onChange={(e) => setNewPersonaId(e.target.value)}
          />

          <label style={styles.label}>Title</label>
          <input
            style={styles.input}
            value={newConversationTitle}
            onChange={(e) => setNewConversationTitle(e.target.value)}
          />

          <button
            style={styles.button}
            onClick={createConversation}
            disabled={creatingConversation || !canCallApi}
          >
            {creatingConversation ? "Creating..." : "Create"}
          </button>
        </div>

        <div style={styles.section}>
          <h3 style={styles.h3}>Conversations</h3>
          <div style={styles.conversationList}>
            {conversations.map((conv) => {
              const id = conv.conversationId || conv.id;
              const title = conv.title || "Untitled conversation";
              const preview = conv.lastMessagePreview || "";
              const isActive = id === selectedConversationId;

              return (
                <button
                  key={id}
                  onClick={() => setSelectedConversationId(id)}
                  style={{
                    ...styles.conversationButton,
                    ...(isActive ? styles.conversationButtonActive : {}),
                  }}
                >
                  <div style={{ fontWeight: 600 }}>{title}</div>
                  {preview ? <div style={styles.previewText}>{preview}</div> : null}
                  <div style={styles.smallText}>
                    {conv.updatedAt ? formatDate(conv.updatedAt) : id}
                  </div>
                </button>
              );
            })}
            {conversations.length === 0 && (
              <div style={styles.smallText}>No conversations yet.</div>
            )}
          </div>
        </div>
      </div>

      <div style={styles.main}>
        <div style={styles.header}>
          <div>
            <h2 style={styles.h2}>
              {selectedConversation?.title || "Conversation"}
            </h2>
            <div style={styles.smallText}>
              {selectedConversationId || "No conversation selected"}
            </div>
          </div>
          {lastUsage && (
            <div style={styles.usageBox}>
              <div><strong>prompt:</strong> {lastUsage.prompt_tokens}</div>
              <div><strong>completion:</strong> {lastUsage.completion_tokens}</div>
              <div><strong>total:</strong> {lastUsage.total_tokens}</div>
            </div>
          )}
        </div>

        {error ? <div style={styles.error}>{error}</div> : null}

        <div style={styles.messages}>
          {loadingConversation ? (
            <div style={styles.smallText}>Loading conversation...</div>
          ) : messages.length === 0 ? (
            <div style={styles.smallText}>No messages yet.</div>
          ) : (
            messages.map((msg) => (
              <div
                key={msg.messageId}
                style={{
                  ...styles.message,
                  ...(msg.role === "user"
                    ? styles.userMessage
                    : styles.assistantMessage),
                }}
              >
                <div style={styles.messageMeta}>
                  <strong>{msg.role}</strong> · {formatDate(msg.createdAt)}
                </div>
                <div style={styles.messageContent}>{msg.content}</div>
              </div>
            ))
          )}
        </div>

        <div style={styles.composer}>
          <textarea
            style={styles.textarea}
            value={messageInput}
            onChange={(e) => setMessageInput(e.target.value)}
            placeholder="Type a message..."
          />
          <button
            style={styles.sendButton}
            onClick={sendMessage}
            disabled={sendingMessage || !selectedConversationId || !messageInput.trim()}
          >
            {sendingMessage ? "Sending..." : "Send"}
          </button>
        </div>
      </div>
    </div>
  );
}

const styles = {
  app: {
    display: "grid",
    gridTemplateColumns: "360px 1fr",
    minHeight: "100vh",
    background: "#f5f7fb",
    color: "#111827",
    fontFamily:
      "Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, sans-serif",
  },
  sidebar: {
    borderRight: "1px solid #e5e7eb",
    background: "#ffffff",
    padding: 20,
    overflowY: "auto",
  },
  main: {
    display: "flex",
    flexDirection: "column",
    minHeight: "100vh",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "flex-start",
    padding: 20,
    borderBottom: "1px solid #e5e7eb",
    background: "#ffffff",
  },
  section: {
    marginTop: 24,
  },
  h2: {
    margin: "0 0 8px 0",
  },
  h3: {
    margin: "0 0 12px 0",
    fontSize: 16,
  },
  label: {
    display: "block",
    marginBottom: 6,
    marginTop: 12,
    fontSize: 14,
    fontWeight: 600,
  },
  input: {
    width: "100%",
    boxSizing: "border-box",
    padding: "10px 12px",
    borderRadius: 10,
    border: "1px solid #d1d5db",
    fontSize: 14,
  },
  textarea: {
    width: "100%",
    boxSizing: "border-box",
    padding: "12px",
    borderRadius: 12,
    border: "1px solid #d1d5db",
    fontSize: 14,
    resize: "vertical",
    minHeight: 110,
  },
  button: {
    marginTop: 12,
    width: "100%",
    padding: "10px 14px",
    borderRadius: 10,
    border: "none",
    background: "#111827",
    color: "white",
    cursor: "pointer",
    fontWeight: 600,
  },
  conversationList: {
    display: "flex",
    flexDirection: "column",
    gap: 8,
  },
  conversationButton: {
    textAlign: "left",
    padding: 12,
    borderRadius: 12,
    border: "1px solid #e5e7eb",
    background: "#fff",
    cursor: "pointer",
  },
  conversationButtonActive: {
    border: "1px solid #111827",
    background: "#f3f4f6",
  },
  previewText: {
    fontSize: 13,
    color: "#374151",
    marginTop: 4,
    whiteSpace: "nowrap",
    overflow: "hidden",
    textOverflow: "ellipsis",
  },
  messages: {
    flex: 1,
    padding: 20,
    overflowY: "auto",
    display: "flex",
    flexDirection: "column",
    gap: 12,
  },
  message: {
    maxWidth: "75%",
    padding: 14,
    borderRadius: 14,
    boxShadow: "0 1px 2px rgba(0,0,0,0.06)",
    whiteSpace: "pre-wrap",
  },
  userMessage: {
    alignSelf: "flex-end",
    background: "#dbeafe",
  },
  assistantMessage: {
    alignSelf: "flex-start",
    background: "#ffffff",
  },
  messageMeta: {
    fontSize: 12,
    opacity: 0.7,
    marginBottom: 6,
  },
  messageContent: {
    lineHeight: 1.5,
  },
  composer: {
    borderTop: "1px solid #e5e7eb",
    background: "#ffffff",
    padding: 20,
  },
  sendButton: {
    marginTop: 12,
    padding: "12px 16px",
    borderRadius: 10,
    border: "none",
    background: "#2563eb",
    color: "white",
    cursor: "pointer",
    fontWeight: 700,
  },
  error: {
    margin: "16px 20px 0 20px",
    padding: 12,
    borderRadius: 10,
    background: "#fee2e2",
    color: "#991b1b",
  },
  smallText: {
    fontSize: 12,
    color: "#6b7280",
  },
  usageBox: {
    fontSize: 13,
    background: "#f9fafb",
    border: "1px solid #e5e7eb",
    borderRadius: 12,
    padding: 12,
  },
  debugCard: {
    marginTop: 12,
    padding: 12,
    borderRadius: 12,
    background: "#f9fafb",
    border: "1px solid #e5e7eb",
    fontSize: 13,
    lineHeight: 1.6,
  },
  debugTitle: {
    fontWeight: 700,
    marginBottom: 6,
  },
};