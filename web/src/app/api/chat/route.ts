import { NextResponse } from "next/server";

import { ask } from "@/lib/ai";
import { prisma } from "@/lib/prisma";
import { getUser } from "@/lib/supabase/server";

type ChatBody = { question?: unknown; conversationId?: unknown };

/** Save the question, get an answer from the AI service, save the answer. */
export async function POST(request: Request) {
  const user = await getUser();
  if (!user?.email) return NextResponse.json({ error: "Not signed in" }, { status: 401 });

  const body = (await request.json().catch(() => ({}))) as ChatBody;
  const question = typeof body.question === "string" ? body.question.trim() : "";
  if (!question || question.length > 2000) {
    return NextResponse.json({ error: "Question must be 1 to 2000 characters" }, { status: 400 });
  }

  await prisma.user.upsert({
    where: { id: user.id },
    update: {},
    create: { id: user.id, email: user.email },
  });

  let conversationId = typeof body.conversationId === "string" ? body.conversationId : null;
  if (conversationId) {
    const owned = await prisma.conversation.findFirst({ where: { id: conversationId, userId: user.id } });
    if (!owned) return NextResponse.json({ error: "Conversation not found" }, { status: 404 });
  } else {
    const created = await prisma.conversation.create({
      data: { userId: user.id, title: question.slice(0, 80) },
    });
    conversationId = created.id;
  }

  const userMessage = await prisma.message.create({
    data: { conversationId, role: "user", content: question },
  });

  let result;
  try {
    result = await ask(question);
  } catch (err) {
    console.error(err);
    return NextResponse.json(
      { error: "The AI service is unavailable. Is it running?", conversationId, userMessage },
      { status: 502 },
    );
  }

  const assistantMessage = await prisma.message.create({
    data: {
      conversationId,
      role: "assistant",
      content: result.answer,
      route: result.route,
      sources: result.sources,
      latencyMs: result.latency_ms,
    },
  });
  // Bump updatedAt so the conversation sorts to the top.
  await prisma.conversation.update({ where: { id: conversationId }, data: { updatedAt: new Date() } });

  return NextResponse.json({ conversationId, userMessage, assistantMessage });
}
