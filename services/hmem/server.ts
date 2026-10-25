import { createServer } from "node:http";
import { mkdirSync } from "node:fs";
import { HMEM } from "./src/index.ts";

const PORT = Number(process.env.HMEM_PORT ?? 7070);
const DIR = process.env.HMEM_DIR ?? "./data";
mkdirSync(DIR, { recursive: true });

// The engine keeps memories on disk in DIR, so they survive a restart.
const hmem = new HMEM({ actor: "recallai", persistDir: DIR });

function send(res: any, code: number, body: unknown) {
  res.writeHead(code, { "Content-Type": "application/json" });
  res.end(JSON.stringify(body));
}

async function readJson(req: any): Promise<any> {
  const chunks: Buffer[] = [];
  for await (const chunk of req) chunks.push(chunk);
  const text = Buffer.concat(chunks).toString("utf8");
  return text ? JSON.parse(text) : {};
}

createServer(async (req, res) => {
  try {
    if (req.method === "GET" && req.url === "/healthz") {
      return send(res, 200, { status: "ok" });
    }
    if (req.method === "POST" && req.url === "/add") {
      const body = await readJson(req);
      const memory = hmem.add({
        content: body.content,
        type: "factual",
        layer: "working",
        tags: body.tags ?? [],
        confidence: 0.9,
        source: body.source,
      });
      return send(res, 200, { id: memory.id, content: memory.content });
    }
    if (req.method === "POST" && req.url === "/query") {
      const body = await readJson(req);
      const result = hmem.query(body.query, {
        topN: body.topN ?? 3,
        threshold: body.threshold ?? 0.1,
      });
      const memories = result.memories.map((item: any) => ({
        id: item.memory.id,
        content: item.memory.content,
        source: item.memory.source,
        tags: item.memory.tags,
        relevance: item.relevance,
      }));
      return send(res, 200, { memories, trace: result.trace });
    }
    return send(res, 404, { error: "not found" });
  } catch (error: any) {
    return send(res, 400, { error: String(error?.message ?? error) });
  }
}).listen(PORT, "127.0.0.1", () => {
  console.log(`H-MEM service listening on http://127.0.0.1:${PORT}`);
});