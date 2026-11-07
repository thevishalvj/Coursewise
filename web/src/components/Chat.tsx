"use client";

import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { createClient } from "@/lib/supabase/client";

type Source = {
  id: number;
  course_code: string | null;
  title: string | null;
  doc_type: string | null;
  url: string | null;
  score: number;
  snippet: string;
};

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  route?: string | null;
  sources?: Source[] | null;
  latencyMs?: number | null;
};

type ConversationSummary = { id: string; title: string; updatedAt: string };

const EXAMPLES = ["What does CS 439 cover?", "Compare CS 312 and CS 314.", "Which course teaches SQL?"];

export default function Chat() {
  const router = useRouter();
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    void loadConversations();
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, pending]);

  async function loadConversations() {
    const res = await fetch("/api/conversations");
    if (res.ok) setConversations((await res.json()).conversations);
  }

  async function openConversation(id: string) {
    setError("");
    const res = await fetch(`/api/conversations/${id}`);
    if (!res.ok) return setError("Could not load that conversation.");
    const { conversation } = await res.json();
    setConversationId(id);
    setMessages(conversation.messages);
  }

  function newChat() {
    setConversationId(null);
    setMessages([]);
    setError("");
  }

  async function deleteConversation(id: string) {
    await fetch(`/api/conversations/${id}`, { method: "DELETE" });
    if (id === conversationId) newChat();
    void loadConversations();
  }

  async function send(question: string) {
    question = question.trim();
    if (!question || pending) return;
    setInput("");
    setError("");
    setPending(true);
    const tempId = `temp-${Date.now()}`;
    setMessages((m) => [...m, { id: tempId, role: "user", content: question }]);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ question, conversationId }),
      });
      const data = await res.json();
      if (data.conversationId) setConversationId(data.conversationId);
      if (!res.ok) throw new Error(data.error ?? "Something went wrong.");
      setMessages((m) => [...m.filter((x) => x.id !== tempId), data.userMessage, data.assistantMessage]);
      void loadConversations();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setPending(false);
    }
  }

  async function signOut() {
    await createClient().auth.signOut();
    router.push("/login");
    router.refresh();
  }

  return (
    <div className="flex h-full">
      <aside className="hidden w-64 shrink-0 flex-col border-r border-border bg-surface md:flex">
        <div className="flex items-center justify-between p-3">
          <span className="font-semibold">Coursewise</span>
          <button onClick={newChat} className="rounded-md border border-border px-2 py-1 text-sm hover:bg-background">
            New chat
          </button>
        </div>
        <nav className="flex-1 overflow-y-auto px-2">
          {conversations.map((c) => (
            <div
              key={c.id}
              className={`group flex items-center rounded-md text-sm ${c.id === conversationId ? "bg-background" : "hover:bg-background"}`}
            >
              <button onClick={() => openConversation(c.id)} className="flex-1 truncate px-2 py-2 text-left">
                {c.title}
              </button>
              <button
                onClick={() => deleteConversation(c.id)}
                aria-label={`Delete ${c.title}`}
                className="px-2 text-muted opacity-0 hover:text-foreground group-hover:opacity-100"
              >
                ×
              </button>
            </div>
          ))}
        </nav>
        <button onClick={signOut} className="m-3 rounded-md px-2 py-1 text-left text-sm text-muted hover:text-foreground">
          Sign out
        </button>
      </aside>

      <main className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-border p-3 md:hidden">
          <span className="font-semibold">Coursewise</span>
          <div className="flex gap-3 text-sm">
            <button onClick={newChat}>New chat</button>
            <button onClick={signOut} className="text-muted">Sign out</button>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto">
          <div className="mx-auto max-w-3xl space-y-6 px-4 py-6">
            {messages.length === 0 && !pending && (
              <div className="pt-16 text-center">
                <h1 className="text-2xl font-semibold">Ask about a UT CS course</h1>
                <p className="mt-2 text-sm text-muted">Answers come only from the course catalog and syllabi.</p>
                <div className="mt-6 flex flex-wrap justify-center gap-2">
                  {EXAMPLES.map((q) => (
                    <button
                      key={q}
                      onClick={() => send(q)}
                      className="rounded-full border border-border px-3 py-1.5 text-sm hover:bg-surface"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            )}
            {messages.map((m) => (m.role === "user" ? <UserBubble key={m.id} text={m.content} /> : <Answer key={m.id} m={m} />))}
            {pending && <p className="text-sm text-muted">Thinking...</p>}
            {error && <p className="text-sm text-red-600">{error}</p>}
            <div ref={bottomRef} />
          </div>
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            void send(input);
          }}
          className="border-t border-border p-3"
        >
          <div className="mx-auto flex max-w-3xl gap-2">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about a course, its grading, or compare two courses"
              maxLength={2000}
              className="flex-1 rounded-lg border border-border bg-background px-3 py-2 outline-none focus:border-accent"
            />
            <button
              type="submit"
              disabled={pending || !input.trim()}
              className="rounded-lg bg-accent px-4 py-2 font-medium text-white disabled:opacity-50"
            >
              Send
            </button>
          </div>
        </form>
      </main>
    </div>
  );
}

function UserBubble({ text }: { text: string }) {
  return (
    <div className="flex justify-end">
      <p className="max-w-[85%] whitespace-pre-wrap rounded-2xl bg-surface px-4 py-2">{text}</p>
    </div>
  );
}

function Answer({ m }: { m: Message }) {
  const sources = m.sources ?? [];
  return (
    <div>
      <p className="whitespace-pre-wrap leading-relaxed">{m.content}</p>
      {sources.length > 0 && (
        <details className="mt-2 text-sm">
          <summary className="cursor-pointer text-muted">
            {sources.length} source{sources.length === 1 ? "" : "s"}
            {m.latencyMs != null && ` · ${(m.latencyMs / 1000).toFixed(1)}s`}
          </summary>
          <ol className="mt-2 space-y-2">
            {sources.map((s) => (
              <li key={s.id} className="rounded-md border border-border p-2">
                <div className="font-medium">
                  [{s.id}] {s.course_code} {s.title}{" "}
                  <span className="font-normal text-muted">({s.doc_type})</span>
                </div>
                <p className="mt-1 text-muted">{s.snippet}</p>
                {s.url && (
                  <a href={s.url} target="_blank" rel="noreferrer" className="mt-1 inline-block text-accent hover:underline">
                    View source
                  </a>
                )}
              </li>
            ))}
          </ol>
        </details>
      )}
    </div>
  );
}
