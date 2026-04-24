import fs from "node:fs";
import process from "node:process";

import { Zalo } from "zca-js";

function nowIso() {
  return new Date().toISOString();
}

function emit(event) {
  process.stdout.write(`${JSON.stringify(event)}\n`);
}

function emitListenerEvent(eventType, summary, detail = "") {
  emit({
    eventType,
    scope: "listener",
    summary,
    detail,
    occurredAt: nowIso(),
  });
}

function fail(summary, detail) {
  emitListenerEvent("listener_error", summary, detail);
  process.exit(1);
}

function parseArgs(argv) {
  const args = { credentialsFile: "" };
  for (let index = 0; index < argv.length; index += 1) {
    if (argv[index] === "--credentials-file") {
      args.credentialsFile = argv[index + 1] || "";
      index += 1;
    }
  }
  return args;
}

function firstNonEmpty(...values) {
  for (const value of values) {
    if (typeof value === "string" && value.trim()) {
      return value.trim();
    }
  }
  return "";
}

function findContent(value, depth = 0) {
  if (depth > 4 || value == null) {
    return "";
  }

  if (typeof value === "string") {
    return value.trim();
  }

  if (Array.isArray(value)) {
    for (const item of value) {
      const found = findContent(item, depth + 1);
      if (found) {
        return found;
      }
    }
    return "";
  }

  if (typeof value === "object") {
    const preferredKeys = [
      "normalUrl",
      "rawUrl",
      "oriUrl",
      "hdUrl",
      "thumbUrl",
      "fileUrl",
      "src",
      "url",
      "href",
      "content",
      "text",
      "caption",
      "title",
      "description",
      "body",
    ];
    for (const key of preferredKeys) {
      const found = findContent(value[key], depth + 1);
      if (found) {
        return found;
      }
    }

    for (const nestedValue of Object.values(value)) {
      const found = findContent(nestedValue, depth + 1);
      if (found) {
        return found;
      }
    }
  }

  return "";
}

function normalizeMessage(message) {
  const data = message?.data ?? {};
  const isGroup =
    Boolean(message?.isGroup)
    || firstNonEmpty(`${message?.threadType ?? ""}`).toLowerCase().includes("group");
  const threadId = firstNonEmpty(
    message?.threadId,
    data?.threadId,
    data?.uidTo,
    data?.uidFrom,
  );
  const msgId = firstNonEmpty(
    data?.msgId,
    data?.msgID,
    data?.cliMsgId,
    data?.id,
    message?.id,
  );
  const rawType = firstNonEmpty(
    data?.msgType,
    data?.type,
    message?.type,
    data?.attachType,
  );
  const content = firstNonEmpty(
    findContent(data?.content),
    findContent(data?.attachments),
    findContent(data?.attach),
    findContent(data?.quote),
    findContent(message?.content),
  );

  return {
    eventType: "new_message",
    scope: "listener",
    summary: "Incoming message received.",
    detail: content,
    occurredAt: nowIso(),
    msgId,
    fromGroupId: isGroup ? threadId : firstNonEmpty(data?.uidFrom, message?.threadId),
    toGroupId: isGroup ? threadId : firstNonEmpty(data?.uidTo, message?.threadId),
    content,
    rawType,
  };
}

function normalizeReceipt(eventType, payload) {
  const items = Array.isArray(payload) ? payload : [payload];
  const firstItem = items[0] ?? {};
  return {
    eventType,
    scope: "listener",
    summary: `${eventType} event received.`,
    detail: firstNonEmpty(firstItem?.msgId, firstItem?.threadId, ""),
    occurredAt: nowIso(),
  };
}

const { credentialsFile } = parseArgs(process.argv.slice(2));
if (!credentialsFile) {
  fail("Listener credentials file is missing.", "Pass --credentials-file <path>.");
}

let credentials;
try {
  credentials = JSON.parse(fs.readFileSync(credentialsFile, "utf8"));
} catch (error) {
  fail("Could not read listener credentials file.", String(error));
}

if (!credentials?.cookie || !credentials?.userAgent || !credentials?.imei) {
  fail(
    "Listener credentials file is invalid.",
    "Expected cookie, userAgent, and imei.",
  );
}

emitListenerEvent("listener_started", "ZCA listener subprocess started.", credentialsFile);

let api;
try {
  const zalo = new Zalo();
  api = await zalo.login(credentials);
} catch (error) {
  fail("ZCA login failed.", String(error));
}

api.listener.on("connected", () => {
  emitListenerEvent("listener_ready", "ZCA listener connected.");
});

api.listener.on("message", (message) => {
  emit(normalizeMessage(message));
});

api.listener.on("delivered_messages", (messages) => {
  emit(normalizeReceipt("delivery_update", messages));
});

api.listener.on("seen_messages", (messages) => {
  emit(normalizeReceipt("delivery_update", messages));
});

api.listener.on("error", (error) => {
  emitListenerEvent("listener_error", "ZCA listener runtime error.", String(error));
});

api.listener.on("closed", (code, reason) => {
  emit({
    eventType: "listener_stopped",
    scope: "listener",
    summary: "ZCA listener stopped.",
    detail: `${code ?? ""} ${reason ?? ""}`.trim(),
    occurredAt: nowIso(),
  });
});

const shutdown = async () => {
  try {
    if (api?.listener?.stop) {
      await api.listener.stop();
    }
  } catch {
    // Best-effort shutdown only.
  }
  emitListenerEvent("listener_stopped", "ZCA listener stopped by tool.");
  process.exit(0);
};

process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);

try {
  await api.listener.start();
} catch (error) {
  fail("Could not start ZCA listener.", String(error));
}
