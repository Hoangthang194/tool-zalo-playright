from browser_automation.infrastructure.playwright_adapter.zalo_live_event_injection_script import (
    ZALO_LIVE_EVENT_INJECTION_SCRIPT,
)


def test_live_event_injection_script_installs_dom_mutation_observer_for_new_messages() -> None:
    assert "MutationObserver" in ZALO_LIVE_EVENT_INJECTION_SCRIPT
    assert "new incoming message" in ZALO_LIVE_EVENT_INJECTION_SCRIPT.casefold()
    assert 'scope: "dom"' in ZALO_LIVE_EVENT_INJECTION_SCRIPT


def test_live_event_injection_script_tracks_conversation_row_preview_and_unread_state() -> None:
    assert ".msg-item" in ZALO_LIVE_EVENT_INJECTION_SCRIPT
    assert "anim-data-id" in ZALO_LIVE_EVENT_INJECTION_SCRIPT
    assert "z-conv-message__preview-message" in ZALO_LIVE_EVENT_INJECTION_SCRIPT
    assert "z-noti-badge" in ZALO_LIVE_EVENT_INJECTION_SCRIPT


def test_live_event_injection_script_extracts_message_content_from_preview() -> None:
    assert "previewContent" in ZALO_LIVE_EVENT_INJECTION_SCRIPT
    assert "New incoming message from" in ZALO_LIVE_EVENT_INJECTION_SCRIPT


def test_live_event_injection_script_refreshes_dom_observer_when_script_version_changes() -> None:
    assert "scriptVersion" in ZALO_LIVE_EVENT_INJECTION_SCRIPT
    assert "conversationObserver.disconnect" in ZALO_LIVE_EVENT_INJECTION_SCRIPT


def test_live_event_injection_script_supports_zca_like_cipher_key_capture_and_decryption() -> None:
    assert "cipherKey" in ZALO_LIVE_EVENT_INJECTION_SCRIPT
    assert "decodeEventData" in ZALO_LIVE_EVENT_INJECTION_SCRIPT
    assert "AES-GCM" in ZALO_LIVE_EVENT_INJECTION_SCRIPT
    assert "DecompressionStream" in ZALO_LIVE_EVENT_INJECTION_SCRIPT


def test_live_event_injection_script_decodes_ws_payloads_into_message_content_and_thread_labels() -> None:
    assert "groupMsgs" in ZALO_LIVE_EVENT_INJECTION_SCRIPT
    assert "msgs" in ZALO_LIVE_EVENT_INJECTION_SCRIPT
    assert "summarizeMessageContent" in ZALO_LIVE_EVENT_INJECTION_SCRIPT
    assert "findConversationLabelByThreadId" in ZALO_LIVE_EVENT_INJECTION_SCRIPT


def test_live_event_injection_script_prioritizes_media_urls_for_image_and_file_messages() -> None:
    assert "normalUrl" in ZALO_LIVE_EVENT_INJECTION_SCRIPT
    assert "rawUrl" in ZALO_LIVE_EVENT_INJECTION_SCRIPT
    assert "hdUrl" in ZALO_LIVE_EVENT_INJECTION_SCRIPT
    assert "thumbUrl" in ZALO_LIVE_EVENT_INJECTION_SCRIPT
    assert "oriUrl" in ZALO_LIVE_EVENT_INJECTION_SCRIPT
    assert "extractPreferredMediaUrl" in ZALO_LIVE_EVENT_INJECTION_SCRIPT


def test_live_event_injection_script_does_not_skip_self_sent_ws_messages() -> None:
    assert 'normalizeText(message.uidFrom) === "0"' not in ZALO_LIVE_EVENT_INJECTION_SCRIPT


def test_live_event_injection_script_tracks_blob_media_urls_from_selected_message_bubbles() -> None:
    assert "URL.createObjectURL" in ZALO_LIVE_EVENT_INJECTION_SCRIPT
    assert "Response.prototype.blob" in ZALO_LIVE_EVENT_INJECTION_SCRIPT
    assert "objectUrlSourceMap" in ZALO_LIVE_EVENT_INJECTION_SCRIPT
    assert "div_LastReceivedMsg_Photo" in ZALO_LIVE_EVENT_INJECTION_SCRIPT
    assert "img.zimg-el" in ZALO_LIVE_EVENT_INJECTION_SCRIPT
    assert "data-qid" in ZALO_LIVE_EVENT_INJECTION_SCRIPT


def test_live_event_injection_script_uses_message_bubble_media_detail_when_preview_is_generic() -> None:
    assert "readSelectedConversationMediaDetail" in ZALO_LIVE_EVENT_INJECTION_SCRIPT
    assert "resolveMediaDetail" in ZALO_LIVE_EVENT_INJECTION_SCRIPT
    assert "hình ảnh" in ZALO_LIVE_EVENT_INJECTION_SCRIPT


def test_live_event_injection_script_rescans_message_pane_after_generic_media_preview() -> None:
    assert "pendingDomMediaEvent" in ZALO_LIVE_EVENT_INJECTION_SCRIPT
    assert "messageObserver" in ZALO_LIVE_EVENT_INJECTION_SCRIPT
    assert "scheduleMessageMediaScan" in ZALO_LIVE_EVENT_INJECTION_SCRIPT
    assert "emitPendingDomMediaEventIfResolved" in ZALO_LIVE_EVENT_INJECTION_SCRIPT
    assert ".message-content-view" in ZALO_LIVE_EVENT_INJECTION_SCRIPT
