from __future__ import annotations

BINDING_NAME = "__browserAutomationEmitZaloLiveEvent"

_SCRIPT_TEMPLATE = """
(() => {
    const stateKey = "__browserAutomationZaloLiveEventState";
    const bindingName = "__BINDING_NAME__";
    const scriptVersion = "2026-04-24-zca-decode-v2";
    const state = window[stateKey] || (window[stateKey] = {});
    const recentEvents = state.recentEvents instanceof Map ? state.recentEvents : new Map();
    const objectUrlSourceMap = state.objectUrlSourceMap instanceof Map ? state.objectUrlSourceMap : new Map();
    state.recentEvents = recentEvents;
    state.objectUrlSourceMap = objectUrlSourceMap;

    if (state.scriptVersion !== scriptVersion) {
        if (state.conversationObserver) {
            state.conversationObserver.disconnect();
            state.conversationObserver = null;
        }
        if (state.conversationObserverTimer) {
            window.clearInterval(state.conversationObserverTimer);
            state.conversationObserverTimer = 0;
        }
        if (state.conversationScanTimer) {
            window.clearTimeout(state.conversationScanTimer);
            state.conversationScanTimer = 0;
        }
        if (state.messageObserver) {
            state.messageObserver.disconnect();
            state.messageObserver = null;
        }
        if (state.messageObserverTimer) {
            window.clearInterval(state.messageObserverTimer);
            state.messageObserverTimer = 0;
        }
        if (state.messageMediaScanTimer) {
            window.clearTimeout(state.messageMediaScanTimer);
            state.messageMediaScanTimer = 0;
        }
        state.conversationSnapshot = null;
        state.conversationObserverBootstrapped = false;
        state.messageObserverBootstrapped = false;
        state.decodeModeActive = false;
        state.pendingDomMediaEvent = null;
        if (state.objectUrlSourceMap instanceof Map) {
            state.objectUrlSourceMap.clear();
        }
        state.scriptVersion = scriptVersion;
    }

    function nowIso() {
        return new Date().toISOString();
    }

    function normalizeText(value) {
        return String(value || "").replace(/\\s+/g, " ").trim();
    }

    function truncateText(value, maxLength = 220) {
        const normalized = normalizeText(value);
        if (!normalized || normalized.length <= maxLength) return normalized;
        return `${normalized.slice(0, maxLength - 3)}...`;
    }

    function isGenericMediaPlaceholder(value) {
        const normalized = normalizeText(value).toLowerCase();
        if (!normalized) return false;

        return [
            "hình ảnh",
            "hinh anh",
            "ảnh",
            "[image]",
            "image",
            "video",
            "[video]",
            "file",
            "[file]",
            "gif",
            "[gif]",
            "sticker",
            "[sticker]",
        ].includes(normalized);
    }

    function safeJsonParse(value) {
        try {
            return JSON.parse(value);
        } catch (_error) {
            return null;
        }
    }

    function safeDecodeURIComponent(value) {
        try {
            return decodeURIComponent(value);
        } catch (_error) {
            return value;
        }
    }

    function decodeUtf8(value) {
        try {
            return new TextDecoder("utf-8").decode(value);
        } catch (_error) {
            return "";
        }
    }

    function decodeBase64ToUint8Array(value) {
        const decoded = atob(String(value || ""));
        const output = new Uint8Array(decoded.length);
        for (let index = 0; index < decoded.length; index += 1) {
            output[index] = decoded.charCodeAt(index);
        }
        return output;
    }

    async function decompressBuffer(bufferSource) {
        if (typeof DecompressionStream !== "function") {
            throw new Error("DecompressionStream is not available in this Chrome session.");
        }

        const inputBuffer = bufferSource instanceof Uint8Array ? bufferSource : new Uint8Array(bufferSource);
        for (const format of ["deflate", "deflate-raw"]) {
            try {
                const decompressed = await new Response(
                    new Blob([inputBuffer]).stream().pipeThrough(new DecompressionStream(format))
                ).arrayBuffer();
                return new Uint8Array(decompressed);
            } catch (_error) {
                continue;
            }
        }

        throw new Error("Could not decompress the encrypted Zalo event payload.");
    }

    async function decryptAesGcmPayload(bufferSource, cipherKey) {
        const encryptedBuffer = bufferSource instanceof Uint8Array ? bufferSource : new Uint8Array(bufferSource);
        if (!cipherKey || encryptedBuffer.byteLength < 48) {
            throw new Error("Missing cipher key or encrypted payload is too short.");
        }

        const iv = encryptedBuffer.slice(0, 16);
        const additionalData = encryptedBuffer.slice(16, 32);
        const dataSource = encryptedBuffer.slice(32);
        const cryptoKey = await crypto.subtle.importKey(
            "raw",
            decodeBase64ToUint8Array(cipherKey),
            "AES-GCM",
            false,
            ["decrypt"]
        );
        const decrypted = await crypto.subtle.decrypt(
            {
                name: "AES-GCM",
                iv,
                tagLength: 128,
                additionalData,
            },
            cryptoKey,
            dataSource,
        );
        return new Uint8Array(decrypted);
    }

    async function decodeEventData(parsed) {
        if (!parsed || typeof parsed !== "object") {
            throw new Error("Decoded Zalo event payload is missing.");
        }

        const rawData = parsed.data;
        const encryptType = parsed.encrypt;

        if (typeof rawData !== "string") {
            throw new Error(`Invalid event data type: ${typeof rawData}`);
        }
        if (typeof encryptType !== "number" || encryptType < 0 || encryptType > 3) {
            throw new Error(`Unsupported encrypt type: ${String(encryptType)}`);
        }

        if (encryptType === 0) {
            return safeJsonParse(rawData);
        }

        const decodedBuffer = decodeBase64ToUint8Array(
            encryptType === 1 ? rawData : safeDecodeURIComponent(rawData)
        );
        const decryptedBuffer = encryptType === 1
            ? decodedBuffer
            : await decryptAesGcmPayload(decodedBuffer, state.cipherKey);
        const inflatedBuffer = encryptType === 3
            ? decryptedBuffer
            : await decompressBuffer(decryptedBuffer);
        const decodedText = decodeUtf8(inflatedBuffer);

        if (!decodedText) {
            throw new Error("The decrypted Zalo event payload was empty.");
        }

        const parsedPayload = safeJsonParse(decodedText);
        if (!parsedPayload) {
            throw new Error("Could not parse the decrypted Zalo event payload.");
        }

        return parsedPayload;
    }

    function readEnvelopeData(decodedPayload) {
        if (!decodedPayload || typeof decodedPayload !== "object") return null;
        if (!decodedPayload.data || typeof decodedPayload.data !== "object") return null;
        return decodedPayload.data;
    }

    function extractContentSnippet(value, depth = 0) {
        if (depth > 3 || value == null) return "";

        if (typeof value === "string") {
            const normalized = normalizeText(value);
            if (!normalized) return "";

            if (
                (normalized.startsWith("{") && normalized.endsWith("}"))
                || (normalized.startsWith("[") && normalized.endsWith("]"))
            ) {
                const nestedValue = safeJsonParse(normalized);
                if (nestedValue) {
                    const nestedSnippet = extractContentSnippet(nestedValue, depth + 1);
                    if (nestedSnippet) return nestedSnippet;
                }
            }

            return normalized;
        }

        if (typeof value === "number" || typeof value === "boolean") {
            return String(value);
        }

        if (Array.isArray(value)) {
            for (const item of value) {
                const snippet = extractContentSnippet(item, depth + 1);
                if (snippet) return snippet;
            }
            return "";
        }

        if (typeof value !== "object") {
            return "";
        }

        for (const key of [
            "content",
            "title",
            "description",
            "name",
            "caption",
            "text",
            "message",
            "msg",
            "href",
            "url",
            "fileName",
            "fileUrl",
            "thumb",
            "item",
            "data",
            "source",
        ]) {
            if (!Object.prototype.hasOwnProperty.call(value, key)) continue;
            const snippet = extractContentSnippet(value[key], depth + 1);
            if (snippet) return snippet;
        }

        if (typeof value.params === "string") {
            const parsedParams = safeJsonParse(value.params);
            if (parsedParams) {
                const snippet = extractContentSnippet(parsedParams, depth + 1);
                if (snippet) return snippet;
            }
        }

        return "";
    }

    function extractPreferredMediaUrl(value, depth = 0) {
        if (depth > 3 || value == null) return "";

        if (typeof value === "string") {
            const normalized = normalizeText(value);
            if (/^https?:\\/\\//i.test(normalized)) {
                return normalized;
            }

            const parsedValue = (
                (normalized.startsWith("{") && normalized.endsWith("}"))
                || (normalized.startsWith("[") && normalized.endsWith("]"))
            )
                ? safeJsonParse(normalized)
                : null;
            if (parsedValue) {
                return extractPreferredMediaUrl(parsedValue, depth + 1);
            }

            return "";
        }

        if (Array.isArray(value)) {
            for (const item of value) {
                const candidate = extractPreferredMediaUrl(item, depth + 1);
                if (candidate) return candidate;
            }
            return "";
        }

        if (typeof value !== "object") {
            return "";
        }

        for (const key of [
            "normalUrl",
            "rawUrl",
            "oriUrl",
            "hdUrl",
            "thumbUrl",
            "previewThumb",
            "thumbnailUrl",
            "fileUrl",
            "href",
            "url",
            "src",
            "imageUrl",
            "mediaUrl",
            "downloadUrl",
            "thumb",
        ]) {
            if (!Object.prototype.hasOwnProperty.call(value, key)) continue;
            const candidate = extractPreferredMediaUrl(value[key], depth + 1);
            if (candidate) return candidate;
        }

        if (typeof value.params === "string") {
            const parsedParams = safeJsonParse(value.params);
            if (parsedParams) {
                const candidate = extractPreferredMediaUrl(parsedParams, depth + 1);
                if (candidate) return candidate;
            }
        }

        for (const key of Object.keys(value)) {
            const candidate = extractPreferredMediaUrl(value[key], depth + 1);
            if (candidate) return candidate;
        }

        return "";
    }

    function resolveBlobSourceUrl(value) {
        const normalized = normalizeText(value);
        if (!normalized) return "";
        if (normalized.startsWith("blob:")) {
            return normalizeText(objectUrlSourceMap.get(normalized) || normalized);
        }
        return normalized;
    }

    function latestMatchingElement(selectors) {
        const matches = [];
        for (const selector of selectors) {
            matches.push(...document.querySelectorAll(selector));
        }

        for (let index = matches.length - 1; index >= 0; index -= 1) {
            const candidate = matches[index];
            if (!(candidate instanceof Element)) continue;
            return candidate;
        }

        return null;
    }

    function readSelectedConversationMediaDetail() {
        const imageElement = latestMatchingElement([
            "[data-id='div_LastReceivedMsg_Photo'] img.zimg-el",
            ".photo-message-v2 img.zimg-el",
            ".chatImageMessage--audit img.zimg-el",
            "img[data-z-element-type='image']",
        ]);
        if (imageElement instanceof HTMLImageElement) {
            const imageUrl = resolveBlobSourceUrl(imageElement.currentSrc || imageElement.src || imageElement.getAttribute("src"));
            if (imageUrl) return imageUrl;

            const qid = normalizeText(
                imageElement.closest("[data-qid]")?.getAttribute("data-qid")
                || imageElement.getAttribute("data-qid")
                || ""
            );
            if (qid) return `qid=${qid}`;
        }

        const photoContainer = latestMatchingElement([
            "[data-id='div_LastReceivedMsg_Photo'][data-qid]",
            ".photo-message-v2[data-qid]",
            ".chatImageMessage--audit[data-qid]",
        ]);
        if (photoContainer instanceof Element) {
            const qid = normalizeText(photoContainer.getAttribute("data-qid"));
            if (qid) return `qid=${qid}`;
        }

        const fileLink = latestMatchingElement([
            ".message-content-view a[href]",
            ".message-non-frame a[href]",
        ]);
        if (fileLink instanceof HTMLAnchorElement) {
            const href = resolveBlobSourceUrl(fileLink.href || fileLink.getAttribute("href"));
            if (href) return href;
        }

        return "";
    }

    function resolveMediaDetail(detail) {
        if (!isGenericMediaPlaceholder(detail)) {
            return detail;
        }

        const selectedMediaDetail = readSelectedConversationMediaDetail();
        if (selectedMediaDetail) {
            return selectedMediaDetail;
        }

        return detail;
    }

    function buildIncomingConversationSummary(conversation, senderName) {
        return senderName && conversation
            ? `New incoming message from '${senderName}' in '${conversation}'.`
            : conversation
                ? `New incoming message detected for '${conversation}'.`
                : "New incoming message detected.";
    }

    function scheduleMessageMediaScan() {
        if (state.messageMediaScanTimer) {
            return;
        }

        state.messageMediaScanTimer = window.setTimeout(() => {
            state.messageMediaScanTimer = 0;
            emitPendingDomMediaEventIfResolved();
        }, 150);
    }

    function emitPendingDomMediaEventIfResolved() {
        const pendingEvent = state.pendingDomMediaEvent;
        if (!pendingEvent || typeof pendingEvent !== "object") {
            return;
        }

        const resolvedDetail = resolveMediaDetail(pendingEvent.detail || "");
        if (!resolvedDetail || isGenericMediaPlaceholder(resolvedDetail)) {
            return;
        }

        emit({
            eventType: "new_message",
            scope: "dom",
            summary: buildIncomingConversationSummary(pendingEvent.conversation || "", pendingEvent.senderName || ""),
            detail: resolvedDetail,
            dedupeKey: buildMessageDedupeKey(
                pendingEvent.rowId || pendingEvent.conversation || "",
                pendingEvent.senderName || pendingEvent.conversation || "",
                resolvedDetail,
            ),
        });
        state.pendingDomMediaEvent = null;
    }

    function messageTypeLabel(messageType) {
        const normalizedType = normalizeText(messageType);
        if (!normalizedType || normalizedType === "webchat") {
            return "";
        }

        const labels = {
            "chat.voice": "[voice]",
            "chat.photo": "[image]",
            "chat.sticker": "[sticker]",
            "chat.doodle": "[doodle]",
            "chat.recommended": "[recommendation]",
            "chat.link": "[link]",
            "chat.video.msg": "[video]",
            "share.file": "[file]",
            "chat.gif": "[gif]",
            "chat.location.new": "[location]",
            "chat.todo": "[todo]",
            "group.poll": "[poll]",
        };
        return labels[normalizedType] || `[${normalizedType}]`;
    }

    function summarizeMessageContent(message) {
        if (!message || typeof message !== "object") {
            return "[message]";
        }

        if (
            message.content
            && typeof message.content === "object"
            && Object.prototype.hasOwnProperty.call(message.content, "deleteMsg")
        ) {
            return "[message deleted]";
        }

        const mediaUrl = extractPreferredMediaUrl(message.content);
        if (mediaUrl) {
            return truncateText(mediaUrl);
        }

        const contentSnippet = extractContentSnippet(message.content);
        const contentLabel = messageTypeLabel(message.msgType);

        if (contentSnippet) {
            if (!contentLabel) {
                return truncateText(contentSnippet);
            }

            if (normalizeText(contentSnippet).toLowerCase() === normalizeText(contentLabel).toLowerCase()) {
                return truncateText(contentSnippet);
            }

            return truncateText(`${contentLabel} ${contentSnippet}`);
        }

        if (contentLabel) {
            return contentLabel;
        }

        return "[message]";
    }

    function selectedConversationLabel() {
        const selectors = [
            ".conv-item.selected .conv-item-title__name .truncate",
            ".conv-item.selected .truncate",
            "#conversation-container header .truncate",
            "header .truncate",
            "[data-id='div_TabMsg_ThrdChItem'] .truncate",
        ];
        for (const selector of selectors) {
            const element = document.querySelector(selector);
            if (!element) continue;
            const text = normalizeText(element.textContent);
            if (text) return text;
        }
        return document.title || location.href;
    }

    function emit(payload) {
        if (typeof window[bindingName] !== "function") return;

        const eventPayload = {
            eventType: String(payload.eventType || "listener"),
            scope: String(payload.scope || "page"),
            summary: String(payload.summary || ""),
            detail: String(payload.detail || ""),
            occurredAt: String(payload.occurredAt || nowIso()),
        };

        const dedupeKey = String(payload.dedupeKey || [
            eventPayload.eventType,
            eventPayload.scope,
            eventPayload.summary,
            eventPayload.detail,
        ].join("|"));
        const lastSeenAt = recentEvents.get(dedupeKey) || 0;
        const currentTime = Date.now();
        if (currentTime - lastSeenAt < 1200) return;
        recentEvents.set(dedupeKey, currentTime);

        try {
            window[bindingName](eventPayload);
        } catch (_error) {
            return;
        }
    }

    function emitListener(summary, detail = "") {
        emit({
            eventType: "listener",
            scope: "system",
            summary,
            detail,
        });
    }

    function classifyReceiptUrl(rawUrl) {
        const url = String(rawUrl || "").toLowerCase();
        if (!url.includes("chat.zalo.me")) return null;
        if (url.includes("delivered")) return "delivered";
        if (url.includes("seen")) return "seen";
        return null;
    }

    function emitReceipt(eventType, rawUrl) {
        if (state.decodeModeActive) return;

        const conversation = selectedConversationLabel();
        const title = eventType === "delivered" ? "Delivered receipt detected" : "Seen receipt detected";
        emit({
            eventType,
            scope: "network",
            summary: conversation ? `${title} for '${conversation}'.` : `${title}.`,
            detail: String(rawUrl || ""),
        });
    }

    function readConversationThreadId(row) {
        if (!(row instanceof Element)) return "";
        return normalizeText(row.getAttribute("anim-data-id") || row.getAttribute("data-id") || "");
    }

    function findConversationLabelByThreadId(threadId) {
        const normalizedThreadId = normalizeText(threadId);
        if (!normalizedThreadId) return "";

        for (const row of conversationRows()) {
            const rowThreadId = readConversationThreadId(row);
            if (rowThreadId !== normalizedThreadId) continue;
            const conversation = readConversationRow(row);
            if (conversation && conversation.name) {
                return conversation.name;
            }
        }

        return "";
    }

    function resolveUserThreadId(message) {
        const senderId = normalizeText(message && message.uidFrom);
        const targetId = normalizeText(message && message.idTo);
        return senderId === "0" ? targetId : senderId;
    }

    function buildMessageDedupeKey(threadId, senderName, detail) {
        return [
            "new_message",
            normalizeText(threadId),
            normalizeText(senderName),
            normalizeText(detail),
        ].join("|");
    }

    function emitDecodedMessage(message, isGroup) {
        const isSelf = normalizeText(message && message.uidFrom) === "0";
        const threadId = isGroup ? normalizeText(message && message.idTo) : resolveUserThreadId(message);
        const senderName = normalizeText(message && (message.dName || message.fromD || ""));
        const conversation = findConversationLabelByThreadId(threadId)
            || (isGroup ? "" : senderName)
            || threadId
            || selectedConversationLabel();
        const detail = resolveMediaDetail(summarizeMessageContent(message));
        state.pendingDomMediaEvent = null;

        emit({
            eventType: "new_message",
            scope: isGroup ? "group" : "user",
            summary: isSelf
                ? (
                    isGroup
                        ? (
                            conversation
                                ? `Sent group message to '${conversation}'.`
                                : "Sent group message."
                        )
                        : (
                            conversation
                                ? `Sent user message to '${conversation}'.`
                                : "Sent user message."
                        )
                )
                : isGroup
                ? (
                    senderName && conversation
                        ? `New group message from '${senderName}' in '${conversation}'.`
                        : conversation
                            ? `New group message detected in '${conversation}'.`
                            : "New group message detected."
                )
                : (
                    conversation
                        ? `New user message from '${conversation}'.`
                        : senderName
                            ? `New user message from '${senderName}'.`
                            : "New user message detected."
                ),
            detail,
            dedupeKey: buildMessageDedupeKey(
                `${isSelf ? "self" : "incoming"}:${threadId || conversation}`,
                senderName || conversation,
                detail,
            ),
        });
    }

    function emitDecodedReceipt(eventType, threadId, detail) {
        const conversation = findConversationLabelByThreadId(threadId) || normalizeText(threadId) || selectedConversationLabel();
        const title = eventType === "delivered" ? "Delivered receipt detected" : "Seen receipt detected";
        emit({
            eventType,
            scope: "receipt",
            summary: conversation ? `${title} for '${conversation}'.` : `${title}.`,
            detail: truncateText(detail || threadId || ""),
            dedupeKey: [eventType, normalizeText(threadId), normalizeText(detail)].join("|"),
        });
    }

    function emitDecodeError(cmd, error) {
        const detail = truncateText(error && error.message ? error.message : error);
        emitListener(`ZCA-style live decode failed for cmd ${cmd}.`, detail);
    }

    async function handleMessageCommand(cmd, parsed) {
        try {
            const decodedPayload = await decodeEventData(parsed);
            const envelopeData = readEnvelopeData(decodedPayload);
            const messages = Array.isArray(envelopeData && (cmd === 521 ? envelopeData.groupMsgs : envelopeData.msgs))
                ? (cmd === 521 ? envelopeData.groupMsgs : envelopeData.msgs)
                : [];

            state.decodeModeActive = true;
            for (const message of messages) {
                if (!message || typeof message !== "object") continue;
                if (
                    message.content
                    && typeof message.content === "object"
                    && Object.prototype.hasOwnProperty.call(message.content, "deleteMsg")
                ) {
                    continue;
                }

                emitDecodedMessage(message, cmd === 521);
            }
        } catch (error) {
            emitDecodeError(cmd, error);
        }
    }

    async function handleReceiptCommand(cmd, parsed) {
        try {
            const decodedPayload = await decodeEventData(parsed);
            const envelopeData = readEnvelopeData(decodedPayload);
            if (!envelopeData) return;

            state.decodeModeActive = true;

            const deliveredMessages = Array.isArray(envelopeData.delivereds) ? envelopeData.delivereds : [];
            const seenMessages = cmd === 522
                ? (Array.isArray(envelopeData.groupSeens) ? envelopeData.groupSeens : [])
                : (Array.isArray(envelopeData.seens) ? envelopeData.seens : []);

            for (const delivered of deliveredMessages) {
                if (!delivered || typeof delivered !== "object") continue;
                const threadId = normalizeText(cmd === 522 ? delivered.groupId : delivered.deliveredUids && delivered.deliveredUids[0]);
                const count = Array.isArray(delivered.deliveredUids) ? delivered.deliveredUids.length : 0;
                emitDecodedReceipt(
                    "delivered",
                    threadId,
                    count > 0 ? `delivered=${count}; msgId=${normalizeText(delivered.msgId)}` : `msgId=${normalizeText(delivered.msgId)}`
                );
            }

            for (const seen of seenMessages) {
                if (!seen || typeof seen !== "object") continue;
                const threadId = normalizeText(cmd === 522 ? seen.groupId : seen.idTo);
                const count = Array.isArray(seen.seenUids) ? seen.seenUids.length : 0;
                emitDecodedReceipt(
                    "seen",
                    threadId,
                    count > 0 ? `seen=${count}; msgId=${normalizeText(seen.msgId)}` : `msgId=${normalizeText(seen.msgId)}`
                );
            }
        } catch (error) {
            emitDecodeError(cmd, error);
        }
    }

    async function handleSocketFrame(buffer) {
        if (!(buffer instanceof ArrayBuffer) || buffer.byteLength < 4) return;

        const view = new DataView(buffer);
        const version = view.getUint8(0);
        const cmd = view.getUint16(1, true);
        const subCmd = view.getUint8(3);
        const rawPayload = decodeUtf8(new Uint8Array(buffer.slice(4)));
        if (!rawPayload) return;

        const parsed = safeJsonParse(rawPayload);
        if (!parsed || typeof parsed !== "object") return;

        if (version === 1 && cmd === 1 && subCmd === 1 && typeof parsed.key === "string") {
            const hadCipherKey = !!state.cipherKey;
            state.cipherKey = parsed.key;
            state.decodeModeActive = true;
            emitListener(
                hadCipherKey
                    ? "Refreshed the ZCA-style cipher key for live message decode."
                    : "Captured the ZCA-style cipher key for live message decode.",
                "cmd=1/subCmd=1"
            );
            return;
        }

        if (version !== 1 || subCmd !== 0) return;

        if (cmd === 501 || cmd === 521) {
            await handleMessageCommand(cmd, parsed);
            return;
        }

        if (cmd === 502 || cmd === 522) {
            await handleReceiptCommand(cmd, parsed);
        }
    }

    function handleWebSocketData(data) {
        try {
            if (data instanceof ArrayBuffer) {
                void handleSocketFrame(data);
                return;
            }

            if (ArrayBuffer.isView(data)) {
                void handleSocketFrame(data.buffer.slice(data.byteOffset, data.byteOffset + data.byteLength));
                return;
            }

            if (typeof Blob !== "undefined" && data instanceof Blob) {
                data.arrayBuffer().then((buffer) => {
                    void handleSocketFrame(buffer);
                }).catch(() => undefined);
            }
        } catch (_error) {
            return;
        }
    }

    function installSocketHooks() {
        let installedNewWrapper = false;

        if (!WebSocket.prototype.dispatchEvent.__browserAutomationZaloWrapped) {
            const previousDispatchEvent = WebSocket.prototype.dispatchEvent;
            const wrappedDispatchEvent = function(event) {
                if (event && event.type === "message") {
                    const liveState = window[stateKey];
                    if (liveState && typeof liveState.handleWebSocketData === "function") {
                        liveState.handleWebSocketData(event.data);
                    }
                }
                return previousDispatchEvent.call(this, event);
            };
            wrappedDispatchEvent.__browserAutomationZaloWrapped = true;
            WebSocket.prototype.dispatchEvent = wrappedDispatchEvent;
            installedNewWrapper = true;
        }

        state.handleWebSocketData = handleWebSocketData;

        if (typeof Response !== "undefined" && typeof Response.prototype.blob === "function" && !Response.prototype.blob.__browserAutomationZaloWrapped) {
            const originalResponseBlob = Response.prototype.blob;
            const wrappedResponseBlob = function() {
                return Promise.resolve(originalResponseBlob.apply(this, arguments)).then((blob) => {
                    if (blob && this && typeof this.url === "string" && this.url) {
                        try {
                            Object.defineProperty(blob, "__browserAutomationSourceUrl", {
                                value: this.url,
                                configurable: true,
                            });
                        } catch (_error) {
                            blob.__browserAutomationSourceUrl = this.url;
                        }
                    }
                    return blob;
                });
            };
            wrappedResponseBlob.__browserAutomationZaloWrapped = true;
            Response.prototype.blob = wrappedResponseBlob;
            installedNewWrapper = true;
        }

        if (typeof URL !== "undefined" && typeof URL.createObjectURL === "function" && !URL.createObjectURL.__browserAutomationZaloWrapped) {
            const originalCreateObjectURL = URL.createObjectURL.bind(URL);
            const wrappedCreateObjectURL = function(object) {
                const createdUrl = originalCreateObjectURL(object);
                const sourceUrl = normalizeText(object && object.__browserAutomationSourceUrl);
                if (createdUrl && sourceUrl) {
                    objectUrlSourceMap.set(createdUrl, sourceUrl);
                    scheduleMessageMediaScan();
                }
                return createdUrl;
            };
            wrappedCreateObjectURL.__browserAutomationZaloWrapped = true;
            URL.createObjectURL = wrappedCreateObjectURL;
            installedNewWrapper = true;
        }

        if (typeof URL !== "undefined" && typeof URL.revokeObjectURL === "function" && !URL.revokeObjectURL.__browserAutomationZaloWrapped) {
            const originalRevokeObjectURL = URL.revokeObjectURL.bind(URL);
            const wrappedRevokeObjectURL = function(objectUrl) {
                objectUrlSourceMap.delete(String(objectUrl || ""));
                return originalRevokeObjectURL(objectUrl);
            };
            wrappedRevokeObjectURL.__browserAutomationZaloWrapped = true;
            URL.revokeObjectURL = wrappedRevokeObjectURL;
            installedNewWrapper = true;
        }

        if (typeof window.fetch === "function" && !window.fetch.__browserAutomationZaloWrapped) {
            const originalFetch = window.fetch;
            const wrappedFetch = function(input, init) {
                const url = typeof input === "string" ? input : (input && input.url) || "";
                const result = originalFetch.apply(this, arguments);
                const liveState = window[stateKey];
                const eventType = classifyReceiptUrl(url);
                if (eventType && liveState && typeof liveState.handleNetworkReceipt === "function") {
                    Promise.resolve(result)
                        .then(() => liveState.handleNetworkReceipt(eventType, url))
                        .catch(() => undefined);
                }
                return result;
            };
            wrappedFetch.__browserAutomationZaloWrapped = true;
            window.fetch = wrappedFetch;
            installedNewWrapper = true;
        }

        if (!XMLHttpRequest.prototype.open.__browserAutomationZaloWrapped) {
            const originalXhrOpen = XMLHttpRequest.prototype.open;
            const wrappedXhrOpen = function(method, url) {
                this.__browserAutomationZaloReceiptUrl = String(url || "");
                return originalXhrOpen.apply(this, arguments);
            };
            wrappedXhrOpen.__browserAutomationZaloWrapped = true;
            XMLHttpRequest.prototype.open = wrappedXhrOpen;
            installedNewWrapper = true;
        }

        if (!XMLHttpRequest.prototype.send.__browserAutomationZaloWrapped) {
            const originalXhrSend = XMLHttpRequest.prototype.send;
            const wrappedXhrSend = function(body) {
                const url = this.__browserAutomationZaloReceiptUrl || "";
                const liveState = window[stateKey];
                const eventType = classifyReceiptUrl(url);
                if (eventType && liveState && typeof liveState.handleNetworkReceipt === "function") {
                    this.addEventListener(
                        "loadend",
                        () => liveState.handleNetworkReceipt(eventType, url),
                        { once: true }
                    );
                }
                return originalXhrSend.apply(this, arguments);
            };
            wrappedXhrSend.__browserAutomationZaloWrapped = true;
            XMLHttpRequest.prototype.send = wrappedXhrSend;
            installedNewWrapper = true;
        }

        try {
            if (navigator && typeof navigator.sendBeacon === "function" && !navigator.sendBeacon.__browserAutomationZaloWrapped) {
                const originalBeacon = navigator.sendBeacon.bind(navigator);
                const wrappedBeacon = function(url, data) {
                    const liveState = window[stateKey];
                    const eventType = classifyReceiptUrl(url);
                    if (eventType && liveState && typeof liveState.handleNetworkReceipt === "function") {
                        liveState.handleNetworkReceipt(eventType, url);
                    }
                    return originalBeacon(url, data);
                };
                wrappedBeacon.__browserAutomationZaloWrapped = true;
                navigator.sendBeacon = wrappedBeacon;
                installedNewWrapper = true;
            }
        } catch (_error) {
            // Ignore browsers that do not allow overriding sendBeacon.
        }

        state.handleNetworkReceipt = (eventType, rawUrl) => emitReceipt(eventType, rawUrl);
        state.socketHooksInstalled = true;
        return installedNewWrapper;
    }

    function conversationRows() {
        return Array.from(
            document.querySelectorAll(".msg-item[data-id='div_TabMsg_ThrdChItem'], .msg-item[anim-data-id]")
        );
    }

    function readConversationRow(row) {
        if (!(row instanceof Element)) return null;

        const rowId = readConversationThreadId(row);
        const name = normalizeText(
            row.querySelector(".conv-item-title__name .truncate, .conv-item-title__name")?.textContent
        );
        const preview = normalizeText(
            row.querySelector(".z-conv-message__preview-message")?.textContent
        );
        const sender = normalizeText(
            row.querySelector(".z-conv-message__preview-sender-name")?.textContent
        );
        const previewContent = preview && sender && preview.startsWith(sender)
            ? normalizeText(preview.slice(sender.length))
            : preview;
        const unread = !!row.querySelector(
            ".z-conv-message.--unread, .z-conv-message[class*='--unread'], .conv-action__unread-v2 .z-noti-badge, .z-noti-badge.--counter"
        );
        const selected = !!row.querySelector(".conv-item.selected") || row.matches(".selected");
        const time = normalizeText(row.querySelector(".preview-time")?.textContent);

        if (!rowId && !name && !preview) {
            return null;
        }

        return {
            id: rowId || `${name}|${preview}`,
            name,
            preview,
            sender,
            previewContent,
            unread,
            selected,
            time,
        };
    }

    function snapshotConversationRows() {
        const snapshot = new Map();
        for (const row of conversationRows()) {
            const stateRow = readConversationRow(row);
            if (!stateRow || !stateRow.id) continue;
            snapshot.set(stateRow.id, stateRow);
        }
        return snapshot;
    }

    function shouldEmitIncomingConversationMessage(current, previous) {
        if (!current || !current.preview) return false;

        const previewChanged = !previous || previous.preview !== current.preview;
        const unreadChanged = current.unread !== (!!previous && previous.unread);
        const senderChanged = !previous || previous.sender !== current.sender;

        if (!(previewChanged || unreadChanged || senderChanged)) {
            return false;
        }

        if (state.decodeModeActive && !current.unread) {
            return false;
        }

        if (current.unread) {
            return true;
        }

        if (current.selected && current.sender && previewChanged) {
            return true;
        }

        return false;
    }

    function emitIncomingConversationMessage(current) {
        const conversation = current.name || selectedConversationLabel();
        const senderName = normalizeText((current.sender || "").replace(/:$/, ""));
        const rawDetail = current.previewContent || current.preview || current.sender || current.time || "";
        const detail = resolveMediaDetail(rawDetail);
        if (current.selected && isGenericMediaPlaceholder(detail)) {
            state.pendingDomMediaEvent = {
                rowId: current.id || conversation,
                conversation,
                senderName,
                detail: rawDetail,
            };
            scheduleMessageMediaScan();
        } else if (!isGenericMediaPlaceholder(detail)) {
            state.pendingDomMediaEvent = null;
        }
        emit({
            eventType: "new_message",
            scope: "dom",
            summary: buildIncomingConversationSummary(conversation, senderName),
            detail,
            dedupeKey: buildMessageDedupeKey(current.id || conversation, senderName || conversation, detail),
        });
    }

    function scanConversationRows() {
        const nextSnapshot = snapshotConversationRows();
        const previousSnapshot = state.conversationSnapshot instanceof Map
            ? state.conversationSnapshot
            : new Map();

        for (const [rowId, current] of nextSnapshot.entries()) {
            const previous = previousSnapshot.get(rowId);
            if (shouldEmitIncomingConversationMessage(current, previous)) {
                emitIncomingConversationMessage(current);
            }
        }

        state.conversationSnapshot = nextSnapshot;
    }

    function scheduleConversationScan() {
        if (state.conversationScanTimer) {
            return;
        }

        state.conversationScanTimer = window.setTimeout(() => {
            state.conversationScanTimer = 0;
            scanConversationRows();
        }, 120);
    }

    function mutationTouchesConversationRows(mutation) {
        if (mutation.type === "characterData") {
            const parent = mutation.target && mutation.target.parentElement;
            return !!(parent && parent.closest(".msg-item"));
        }

        if (mutation.type === "attributes") {
            const target = mutation.target;
            return target instanceof Element && !!target.closest(".msg-item");
        }

        const changedNodes = [...mutation.addedNodes, ...mutation.removedNodes];
        for (const node of changedNodes) {
            if (!(node instanceof Element)) continue;
            if (
                node.matches(".msg-item, .z-conv-message__preview-message, .z-noti-badge, .preview-time")
                || !!node.querySelector(".msg-item, .z-conv-message__preview-message, .z-noti-badge, .preview-time")
            ) {
                return true;
            }
        }
        return false;
    }

    function installConversationObserver() {
        if (state.conversationObserver || !document.body) {
            return false;
        }

        state.conversationSnapshot = snapshotConversationRows();
        const observer = new MutationObserver((mutations) => {
            for (const mutation of mutations) {
                if (mutationTouchesConversationRows(mutation)) {
                    scheduleConversationScan();
                    return;
                }
            }
        });

        observer.observe(document.body, {
            subtree: true,
            childList: true,
            characterData: true,
            attributes: true,
            attributeFilter: ["class"],
        });
        state.conversationObserver = observer;
        return true;
    }

    function ensureConversationObserver() {
        if (state.conversationObserver) {
            return;
        }

        if (document.body) {
            installConversationObserver();
            return;
        }

        if (state.conversationObserverBootstrapped) {
            return;
        }

        state.conversationObserverBootstrapped = true;
        state.conversationObserverTimer = window.setInterval(() => {
            if (!document.body) {
                return;
            }
            window.clearInterval(state.conversationObserverTimer);
            state.conversationObserverTimer = 0;
            state.conversationObserverBootstrapped = false;
            installConversationObserver();
        }, 250);
    }

    function messageMutationTouchesMedia(mutation) {
        if (mutation.type === "characterData") {
            const parent = mutation.target && mutation.target.parentElement;
            return !!(parent && parent.closest(".message-content-view, .message-non-frame"));
        }

        if (mutation.type === "attributes") {
            const target = mutation.target;
            return target instanceof Element && !!target.closest(".message-content-view, .message-non-frame");
        }

        const changedNodes = [...mutation.addedNodes, ...mutation.removedNodes];
        for (const node of changedNodes) {
            if (!(node instanceof Element)) continue;
            if (
                node.matches(
                    ".message-content-view, .message-non-frame, .photo-message-v2, .chatImageMessage--audit, [data-id='div_LastReceivedMsg_Photo'], img.zimg-el, img[data-z-element-type='image'], a[href]"
                )
                || !!node.querySelector(
                    ".message-content-view, .message-non-frame, .photo-message-v2, .chatImageMessage--audit, [data-id='div_LastReceivedMsg_Photo'], img.zimg-el, img[data-z-element-type='image'], a[href]"
                )
            ) {
                return true;
            }
        }

        return false;
    }

    function installMessageObserver() {
        if (state.messageObserver || !document.body) {
            return false;
        }

        const observer = new MutationObserver((mutations) => {
            if (!state.pendingDomMediaEvent) {
                return;
            }

            for (const mutation of mutations) {
                if (messageMutationTouchesMedia(mutation)) {
                    scheduleMessageMediaScan();
                    return;
                }
            }
        });

        observer.observe(document.body, {
            subtree: true,
            childList: true,
            characterData: true,
            attributes: true,
            attributeFilter: ["class", "src", "href"],
        });
        state.messageObserver = observer;
        return true;
    }

    function ensureMessageObserver() {
        if (state.messageObserver) {
            return;
        }

        if (document.body) {
            installMessageObserver();
            return;
        }

        if (state.messageObserverBootstrapped) {
            return;
        }

        state.messageObserverBootstrapped = true;
        state.messageObserverTimer = window.setInterval(() => {
            if (!document.body) {
                return;
            }
            window.clearInterval(state.messageObserverTimer);
            state.messageObserverTimer = 0;
            state.messageObserverBootstrapped = false;
            installMessageObserver();
        }, 250);
    }

    const socketHooksInstalled = installSocketHooks();
    ensureConversationObserver();
    ensureMessageObserver();

    if (socketHooksInstalled) {
        emitListener("Live event hooks installed on the active Zalo tab with ZCA-style decode support.", location.href);
        return "installed";
    }

    emitListener("Live event hooks were already active on the current Zalo tab and handlers were refreshed.", location.href);
    return "already_installed";
})()
"""

ZALO_LIVE_EVENT_INJECTION_SCRIPT = _SCRIPT_TEMPLATE.replace("__BINDING_NAME__", BINDING_NAME)
