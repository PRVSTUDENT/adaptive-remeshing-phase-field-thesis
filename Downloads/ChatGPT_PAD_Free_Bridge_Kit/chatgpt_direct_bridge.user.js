// ==UserScript==
// @name         ChatGPT - Direct Local Bridge (PAD-Free)
// @namespace    chatgpt-autonomous-bridge-response
// @version      2.0.1
// @description  PAD-free correlated supervisor handoffs via authenticated localhost bridge. Uses original v1.5 completed-response guards.
// @match        https://chatgpt.com/*
// @grant        GM_xmlhttpRequest
// @connect      127.0.0.1
// @run-at       document-idle
// ==/UserScript==

(function () {
    'use strict';

    // Paste the secret from:
    // $env:USERPROFILE\OpenClawPAD\ChatGPTBridge\direct_bridge\secret.txt
    // NEVER paste that token into ChatGPT or commit it to Git.
    const BRIDGE_TOKEN = 'REPLACE_WITH_YOUR_LOCAL_SECRET';
    const BRIDGE_URL = 'http://127.0.0.1:8765';
    const DIRECT_MODE = true;
    const DIRECT_POLL_MS = 2500;
    let directContext = null;
    let directPollBusy = false;
    let directPosting = false;
    let lastDirectError = '';
    // A duplicated tab can inherit sessionStorage. Never inherit its claim.
    // Reloads have a new identity and must reconcile an old durable claim.
    const directClientId = 'tab_' + crypto.randomUUID().replace(/-/g, '');
    const DIRECT_SENT_KEY = 'chatgpt_direct_bridge_sent_id_v1';

    function bridgeHttp(method, path, data = null) {
        return new Promise((resolve, reject) => {
            GM_xmlhttpRequest({
                method,
                url: BRIDGE_URL + path,
                headers: {
                    'X-Bridge-Token': BRIDGE_TOKEN,
                    'Content-Type': 'application/json'
                },
                data: data ? JSON.stringify(data) : undefined,
                timeout: 10000,
                onload: reply => {
                    let parsed;
                    try { parsed = JSON.parse(reply.responseText); }
                    catch (_) { reject(new Error('Non-JSON localhost response')); return; }
                    if (reply.status < 200 || reply.status >= 300) {
                        reject(new Error('HTTP ' + reply.status + ': ' +
                            (parsed.error || parsed.status || 'UNKNOWN')));
                        return;
                    }
                    resolve(parsed);
                },
                ontimeout: () => reject(new Error('Local bridge HTTP timeout')),
                onerror: () => reject(new Error('Local bridge HTTP/network failure'))
            });
        });
    }

    function normalizeComposerText(s) {
        return String(s || '').replace(/\r\n?/g, '\n')
          .replace(/\u00a0/g, ' ').trim();
    }

    function composerContainsExactRequest(text) {
        const composer = findComposer();
        if (!composer) return false;
        const expected = normalizeComposerText(text);
        // Only normalize line endings/renderer whitespace; never accept a
        // changed middle merely because the marker, length and tail match.
        const actual = normalizeComposerText(composer.innerText || composer.textContent);
        return actual === expected;
    }

    async function pollDirectBridge() {
        if (!DIRECT_MODE || directPollBusy || directPosting ||
            sendWatchActive || responseWatchActive) return;
        if (!BRIDGE_TOKEN || BRIDGE_TOKEN.startsWith('REPLACE_WITH_')) return;
        directPollBusy = true;
        try {
            const tx = await bridgeHttp('GET',
                '/next?client_id=' + encodeURIComponent(directClientId));
            if (tx.status !== 'READY') return;
            if (!tx.handoff_id || !tx.prompt || !tx.request_sha256) return;
            if (sessionStorage.getItem(DIRECT_SENT_KEY) === tx.handoff_id) {
                // A tab reload is not proof that the earlier send was unsuccessful.
                // Never send the same logical transaction twice automatically.
                lastDirectError = 'Request already sent in this tab; no automatic replay';
                setBridgeState('ERROR');
                showStatus('⚠️ Direct bridge pending\n' + tx.handoff_id +
                           '\nPreviously sent; inspect before recovery.');
                return;
            }
            if (directContext && directContext.handoff_id === tx.handoff_id) return;
            if (tx.handoff_id !== extractHandoffId(tx.prompt)) {
                throw new Error('Request body/ID mismatch');
            }
            const composer = findComposer();
            if (!composer) return; // Keep claim, report missing UI; no blind send.
            if (normalizeComposerText(composer.innerText || composer.textContent)) {
                lastDirectError = 'Composer not empty; refusing to overwrite user input';
                showStatus('⚠️ Direct bridge: composer not empty\n' + tx.handoff_id);
                return;
            }
            directContext = tx;
            startBridgePaste(tx.prompt); // existing verified send/response watcher
            composer.focus();
            const inserted = document.execCommand('insertText', false, tx.prompt);
            await new Promise(resolve => setTimeout(resolve, 300));
            if (!inserted || !composerContainsExactRequest(tx.prompt)) {
                stopSendWatch();
                lastDirectError = 'DIRECT_COMPOSER_INSERTION_NOT_VERIFIED';
                setBridgeState('ERROR');
                showStatus('❌ Direct injection not verified; no send\n' + tx.handoff_id);
                return;
            }
            console.log('[Direct Bridge] Local request safely inserted:', tx.handoff_id);
        } catch (error) {
            if (String(error.message).includes('HTTP 403')) {
                lastDirectError = 'Token invalid. Check local secret in userscript.';
                showStatus('❌ Local bridge token rejected; no send.');
            } else if (String(error.message).includes('HTTP 409')) {
                lastDirectError = String(error.message);
                showStatus('❌ Local bridge refused request; inspect claim/lock.');
            } else {
                // Server may simply not be running yet. Avoid noisy alerts.
                console.debug('[Direct Bridge]', error.message);
            }
        } finally {
            directPollBusy = false;
        }
    }


    // ============================================================
    // CONFIGURATION
    // ============================================================

    // Minimum time after paste before auto-send is allowed.
    const MIN_WAIT_SECONDS = 15;

    // Final safety latch once the live Send button is ready.
    const READY_STABLE_MS = 2500;

    // Composer must be quiet this long BEFORE the final latch starts.
    const DOM_QUIET_MS = 1200;

    // Auto-send polling frequency.
    const SEND_POLL_MS = 400;

    // Maximum time allowed for a pasted bridge prompt to become sendable.
    const SEND_MAX_WAIT_MS = 5 * 60 * 1000;

    // Response monitoring.
    const RESPONSE_POLL_MS = 500;
    const RESPONSE_STABLE_MS = 7000;
    const RESPONSE_MAX_WAIT_MS = 30 * 60 * 1000;

    // Final success/error popup duration.
    const RESULT_POPUP_MS = 30 * 1000;

    // ============================================================
    // STATE
    // ============================================================

    let sendWatchActive = false;
    let responseWatchActive = false;

    let currentHandoffId = null;

    let pasteStartedAt = 0;
    let pasteLength = 0;

    let sendReadySince = 0;
    let lastComposerMutationAt = 0;

    let sendInterval = null;
    let responseInterval = null;

    let composerObserver = null;
    let cachedComposerForm = null;

    let responseStartedAt = 0;

    let baselineAssistantCount = 0;
    let baselineAssistantElement = null;
    let baselineAssistantText = '';
    let baselineAssistantIdentity = null;

    // Immutable pre-send snapshots. Never accept a re-rendered old turn.
    let baselineAssistantIds = new Set();
    let baselineAssistantNodes = new Set();
    let baselineUserIds = new Set();
    let baselineUserNodes = new Set();

    // Explicit send acknowledgement: the submitted user turn must exist.
    let acceptedUserId = null;
    let acceptedUserNode = null;

    // A completed action bar belonging to THIS assistant turn is mandatory.
    let completedActionsSince = 0;
    let responseCandidateId = null;
    let responseCandidateNode = null;

    let lastResponseText = '';
    let responseStableSince = 0;

    let popupTimer = null;

    // ============================================================
    // BASIC DOM HELPERS
    // ============================================================

    function isVisible(element) {
        if (!element) return false;
        if (!element.isConnected) return false;

        const rect = element.getBoundingClientRect();

        if (rect.width <= 0 || rect.height <= 0) {
            return false;
        }

        const style = window.getComputedStyle(element);

        if (
            style.display === 'none' ||
            style.visibility === 'hidden' ||
            Number(style.opacity) === 0
        ) {
            return false;
        }

        return true;
    }

    // ============================================================
    // LIVE COMPOSER DETECTION
    // ============================================================

    function findComposer() {
        const selectors = [
            '#prompt-textarea',
            'textarea[data-testid="prompt-textarea"]',
            'div#prompt-textarea[contenteditable="true"]',
            'div[contenteditable="true"][data-lexical-editor="true"]',
            'form div[contenteditable="true"]'
        ];

        for (const selector of selectors) {
            const elements = document.querySelectorAll(selector);

            for (const element of elements) {
                if (isVisible(element)) {
                    return element;
                }
            }
        }

        return null;
    }

    function getCurrentComposerForm() {
        const composer = findComposer();

        if (!composer) {
            return null;
        }

        const form = composer.closest('form');

        if (!form || !form.isConnected) {
            return null;
        }

        return form;
    }

    // ============================================================
    // LIVE SEND BUTTON DETECTION
    // ============================================================

    function findSendButton() {
        const selectors = [
            // Current ChatGPT DOM.
            'button[type="submit"][aria-label="Send"]',
            'button[aria-label="Send"]',

            // Legacy fallbacks.
            '#composer-submit-button',
            'button[data-testid="send-button"]',
            'button[aria-label="Send prompt"]'
        ];

        const currentForm = getCurrentComposerForm();

        const scopes = [];

        // Current live composer form gets first priority.
        if (currentForm && currentForm.isConnected) {
            scopes.push(currentForm);
        }

        // Cached form only if still attached.
        if (
            cachedComposerForm &&
            cachedComposerForm.isConnected &&
            cachedComposerForm !== currentForm
        ) {
            scopes.push(cachedComposerForm);
        }

        // Last-resort global lookup.
        scopes.push(document);

        for (const scope of scopes) {
            for (const selector of selectors) {
                const buttons = scope.querySelectorAll(selector);

                for (const button of buttons) {
                    if (isVisible(button)) {
                        return button;
                    }
                }
            }
        }

        return null;
    }

    function isSendReady(button) {
        if (!button) return false;
        if (!button.isConnected) return false;
        if (!isVisible(button)) return false;

        if (button.disabled) {
            return false;
        }

        if (button.getAttribute('aria-disabled') === 'true') {
            return false;
        }

        const style = window.getComputedStyle(button);

        if (style.pointerEvents === 'none') {
            return false;
        }

        return true;
    }

    // ============================================================
    // BRIDGE HANDOFF ID
    // ============================================================

    function extractHandoffId(text) {
        /*
         * Only accept a real bridge line, for example:
         *
         * [BRIDGE_HANDOFF_ID=HND-TEST-001]
         */
        const match = text.match(
            /^\s*\[BRIDGE_HANDOFF_ID=(HND-[A-Za-z0-9_-]+)\]\s*$/m
        );

        return match ? match[1] : null;
    }

    // ============================================================
    // COMPOSER / ATTACHMENT PROCESSING
    // ============================================================

    function isComposerProcessing() {
        const currentForm = getCurrentComposerForm();

        const scope =
            currentForm ||
            (
                cachedComposerForm &&
                cachedComposerForm.isConnected
                    ? cachedComposerForm
                    : document
            );

        const selectors = [
            '[role="progressbar"]',
            '[aria-label*="uploading" i]',
            '[aria-label*="processing" i]',
            '[data-testid*="upload-progress" i]',
            '[data-testid*="loading" i]',
            '[class*="uploading" i]'
        ];

        for (const selector of selectors) {
            const elements = scope.querySelectorAll(selector);

            for (const element of elements) {
                if (isVisible(element)) {
                    return true;
                }
            }
        }

        return false;
    }

    // ============================================================
    // STATUS PANEL
    // ============================================================

    const panel = document.createElement('div');
    panel.id = 'ag-bridge-status-panel';

    const statusText = document.createElement('div');
    statusText.id = 'ag-bridge-status-text';

    const cancelButton = document.createElement('button');
    cancelButton.id = 'ag-bridge-cancel-button';

    panel.appendChild(statusText);
    panel.appendChild(cancelButton);

    document.body.appendChild(panel);

    function resetPanelStyle() {
        Object.assign(panel.style, {
            position: 'fixed',
            right: '20px',
            bottom: '105px',

            zIndex: '2147483647',

            minWidth: '260px',
            maxWidth: '390px',

            padding: '12px 14px',

            borderRadius: '12px',

            background: 'rgba(22,22,22,0.97)',
            color: '#ffffff',

            border: '1px solid rgba(255,255,255,0.20)',

            boxShadow: '0 7px 28px rgba(0,0,0,0.42)',

            fontFamily:
                'system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif',

            fontSize: '13px',
            lineHeight: '1.45',

            display: 'none'
        });

        Object.assign(statusText.style, {
            whiteSpace: 'pre-line'
        });

        Object.assign(cancelButton.style, {
            width: '100%',

            marginTop: '10px',
            padding: '8px',

            borderRadius: '7px',

            border:
                '1px solid rgba(255,255,255,0.25)',

            background: 'transparent',
            color: '#ffffff',

            cursor: 'pointer',

            display: 'none'
        });
    }

    resetPanelStyle();

    function setBridgeState(state) {
        panel.dataset.bridgeState = state;
        panel.dataset.bridgeHandoffId =
            currentHandoffId || '';

        document.documentElement.dataset.agBridgeStatus =
            state;

        document.documentElement.dataset.agBridgeId =
            currentHandoffId || '';
    }

    function showStatus(text, cancelLabel = null) {
        if (popupTimer) {
            clearTimeout(popupTimer);
            popupTimer = null;
        }

        statusText.textContent = text;

        if (cancelLabel) {
            cancelButton.textContent = cancelLabel;
            cancelButton.style.display = 'block';
        } else {
            cancelButton.style.display = 'none';
        }

        panel.style.display = 'block';
    }

    function hideStatusAfter(milliseconds) {
        if (popupTimer) {
            clearTimeout(popupTimer);
        }

        popupTimer = setTimeout(() => {
            panel.style.display = 'none';

            resetPanelStyle();

            setBridgeState('IDLE');

            popupTimer = null;
        }, milliseconds);
    }

    // ============================================================
    // CONNECTION-PROBLEM DETECTION
    // ============================================================

    function isInsideConversationMessage(element) {
        if (!element) {
            return false;
        }

        return Boolean(
            element.closest('[data-message-author-role]') ||
            element.closest('[data-testid^="conversation-turn-"]') ||
            element.closest(
                '[data-chatgpt-search-unit-key$=":assistant"]'
            ) ||
            element.closest(
                '[data-chatgpt-search-unit-key$=":user"]'
            ) ||
            element.closest(
                '[data-content-search-unit-key$=":assistant"]'
            ) ||
            element.closest(
                '[data-content-search-unit-key$=":user"]'
            )
        );
    }

    function getChatGPTConnectionProblem() {
        /*
         * NEVER scan document.body.innerText.
         *
         * Previous chat text may itself contain words such as
         * "Connection interrupted", which caused false positives.
         */

        const phrases = [
            {
                text:
                    'Connection interrupted. Waiting for the complete answer',
                code:
                    'CONNECTION_INTERRUPTED'
            },
            {
                text:
                    'Network error',
                code:
                    'NETWORK_ERROR'
            },
            {
                text:
                    'Something went wrong',
                code:
                    'SOMETHING_WENT_WRONG'
            }
        ];

        const semanticSelectors = [
            '[role="alert"]',
            '[role="status"]',
            '[data-testid*="error" i]',
            '[data-testid*="network" i]',
            '[data-testid*="connection" i]'
        ];

        for (const selector of semanticSelectors) {
            const nodes =
                document.querySelectorAll(selector);

            for (const node of nodes) {
                if (!isVisible(node)) continue;

                if (
                    node === panel ||
                    panel.contains(node)
                ) {
                    continue;
                }

                if (isInsideConversationMessage(node)) {
                    continue;
                }

                const text = (
                    node.innerText ||
                    node.textContent ||
                    ''
                ).trim();

                if (!text) continue;
                if (text.length > 500) continue;

                for (const phrase of phrases) {
                    if (
                        text.includes(
                            phrase.text
                        )
                    ) {
                        return phrase.code;
                    }
                }
            }
        }

        /*
         * Some transient ChatGPT banners have no role/testid.
         *
         * Search small visible standalone nodes, but explicitly
         * exclude conversation content.
         */
        const genericNodes =
            document.querySelectorAll(
                'div, span, p'
            );

        for (const node of genericNodes) {
            if (!isVisible(node)) continue;

            if (
                node === panel ||
                panel.contains(node)
            ) {
                continue;
            }

            if (isInsideConversationMessage(node)) {
                continue;
            }

            if (node.children.length > 6) {
                continue;
            }

            const text = (
                node.innerText ||
                node.textContent ||
                ''
            ).trim();

            if (!text) continue;
            if (text.length > 220) continue;

            for (const phrase of phrases) {
                if (
                    text === phrase.text ||
                    text.includes(
                        phrase.text
                    )
                ) {
                    return phrase.code;
                }
            }
        }

        return null;
    }

    // ============================================================
    // ASSISTANT MESSAGE DETECTION
    // ============================================================

    function getAssistantMessages() {
        /*
         * CURRENT ChatGPT DOM.
         */
        const modern =
            Array.from(
                document.querySelectorAll(
                    '[data-chatgpt-search-unit-key$=":assistant"]'
                )
            ).filter(
                isVisible
            );

        if (modern.length) {
            return modern;
        }

        /*
         * Secondary modern fallback.
         */
        const contentUnits =
            Array.from(
                document.querySelectorAll(
                    '[data-content-search-unit-key$=":assistant"]'
                )
            ).filter(
                isVisible
            );

        if (contentUnits.length) {
            return contentUnits;
        }

        /*
         * Legacy fallback.
         */
        return Array.from(
            document.querySelectorAll(
                '[data-message-author-role="assistant"]'
            )
        ).filter(
            isVisible
        );
    }

    function getUserMessages() {
        const selectors = [
            '[data-chatgpt-search-unit-key$=":user"]',
            '[data-content-search-unit-key$=":user"]',
            '[data-message-author-role="user"]'
        ];
        for (const selector of selectors) {
            const found = Array.from(document.querySelectorAll(selector))
                .filter(isVisible);
            if (found.length) return found;
        }
        return [];
    }

    function getAssistantText(message) {
        if (!message) {
            return '';
        }
        if (directContext) {
            const code = message.querySelector('pre code');
            if (code && code.textContent && code.textContent.trim().startsWith('{')) {
                return code.textContent.trim();
            }
        }

        /*
         * Prefer only the actual assistant response markdown.
         *
         * This prevents toolbar labels such as Copy, Share,
         * Regenerate, etc. entering the copied response.
         */
        const markdown =
            message.querySelector(
                '[data-markdown-text-style="assistant-message"]'
            );

        // New ChatGPT writing blocks expose their actual editable draft here.
        // The visual text includes controls/screen-reader labels (e.g. "Writing").
        if (markdown) {
            const drafts = markdown.querySelectorAll(
                '[data-testid="chatgpt-writing-block"][data-markdown-copy-text]'
            );
            if (drafts.length === 1) {
                const draft = drafts[0];
                const outside = (markdown.innerText || '')
                    .replace(draft.innerText || '', '')
                    .trim();
                if (!outside || outside === 'Writing') {
                    return (draft.getAttribute('data-markdown-copy-text') || '').trim();
                }
            }
        }

        if (markdown) {
            return (
                markdown.innerText ||
                markdown.textContent ||
                ''
            ).trim();
        }

        const markdownRoot =
            message.querySelector(
                '[class*="MarkdownRoot"]'
            );

        if (markdownRoot) {
            return (
                markdownRoot.innerText ||
                markdownRoot.textContent ||
                ''
            ).trim();
        }

        return (
            message.innerText ||
            message.textContent ||
            ''
        ).trim();
    }

    function getAssistantIdentity(message) {
        if (!message) {
            return null;
        }

        /*
         * Current ChatGPT identifiers.
         */
        const searchMessageIds =
            message.getAttribute(
                'data-chatgpt-search-message-ids'
            );

        if (searchMessageIds) {
            return (
                `search-message:${searchMessageIds}`
            );
        }

        const unitKey =
            message.getAttribute(
                'data-chatgpt-search-unit-key'
            ) ||
            message.getAttribute(
                'data-content-search-unit-key'
            );

        if (unitKey) {
            return (
                `unit:${unitKey}`
            );
        }

        /*
         * Legacy identifiers.
         */
        const directId =
            message.getAttribute(
                'data-message-id'
            );

        if (directId) {
            return (
                `message:${directId}`
            );
        }

        const idContainer =
            message.closest(
                '[data-message-id]'
            );

        if (idContainer) {
            const id =
                idContainer.getAttribute(
                    'data-message-id'
                );

            if (id) {
                return (
                    `message:${id}`
                );
            }
        }

        const turn =
            message.closest(
                '[data-testid^="conversation-turn-"]'
            );

        if (turn) {
            const testId =
                turn.getAttribute(
                    'data-testid'
                );

            if (testId) {
                return (
                    `turn:${testId}`
                );
            }
        }

        return null;
    }

    function captureAssistantBaseline() {
        // Snapshot ALL currently known messages before clicking Send.
        // The old implementation looked only at the last visible assistant and
        // treated a React node replacement as proof of a new reply.
        const assistants = getAssistantMessages();
        const users = getUserMessages();
        const latest = assistants.length ? assistants[assistants.length - 1] : null;

        return {
            count: assistants.length,
            latest: latest,
            text: getAssistantText(latest),
            identity: getAssistantIdentity(latest),
            assistantIds: new Set(assistants.map(getAssistantIdentity).filter(Boolean)),
            assistantNodes: new Set(assistants),
            userIds: new Set(users.map(getAssistantIdentity).filter(Boolean)),
            userNodes: new Set(users)
        };
    }

    function getAcknowledgedUserTurn() {
        const users = getUserMessages();

        // Keep the initial submitted turn locked; do not silently attach a
        // second handoff to someone else's user message.
        if (acceptedUserId || acceptedUserNode) {
            for (const message of users) {
                const id = getAssistantIdentity(message);
                if (acceptedUserId ? id === acceptedUserId : message === acceptedUserNode) {
                    acceptedUserNode = message; // tolerate a React re-render
                    return message;
                }
            }
            return null;
        }

        for (const message of users) {
            const id = getAssistantIdentity(message);
            if (baselineUserNodes.has(message)) continue;
            if (id && baselineUserIds.has(id)) continue;

            if (directContext) {
                const submittedText = (message.innerText || message.textContent || '');
                if (!submittedText.includes('[BRIDGE_HANDOFF_ID=' + currentHandoffId + ']')) {
                    continue; // This is not OUR submitted user message.
                }
            }
            acceptedUserId = id || null;
            acceptedUserNode = message;
            console.log('[Autonomous Bridge] New user turn acknowledged:', id);
            return message;
        }
        return null;
    }

    function isAfterNode(node, earlier) {
        if (!node || !earlier || node === earlier) return false;
        // Node.compareDocumentPosition is DOM-native and works even if the
        // conversation dynamically reorders or virtualizes its turn wrappers.
        return Boolean(earlier.compareDocumentPosition(node) & Node.DOCUMENT_POSITION_FOLLOWING);
    }

    function findNewAssistantMessage() {
        // MANDATORY handshake 1: ChatGPT actually appended THIS send's user turn.
        const newUser = getAcknowledgedUserTurn();
        if (!newUser) return null;

        const messages = getAssistantMessages();
        let latest = null;
        for (const message of messages) {
            const id = getAssistantIdentity(message);

            // Never copy an assistant turn present before Send, even if React
            // has replaced its DOM node or its text has changed on hydration.
            if (baselineAssistantNodes.has(message)) continue;
            if (id && baselineAssistantIds.has(id)) continue;

            // MANDATORY handshake 2: this assistant appears AFTER the newly
            // acknowledged user message in the conversation DOM.
            if (!isAfterNode(message, newUser)) continue;
            latest = message;
        }
        return latest;
    }

    // ============================================================
    // GENERATION STATE
    // ============================================================

    function isChatGPTGenerating() {
        const selectors = [
            'button[data-testid="stop-button"]',
            'button[aria-label*="stop generating" i]',
            'button[aria-label*="stop streaming" i]',
            'button[aria-label*="stop response" i]',
            'button[aria-label="Stop"]',
            'button[aria-label="Stop generating"]',
            'button[data-testid="stop-generating-button"]'
        ];

        for (const selector of selectors) {
            const nodes =
                document.querySelectorAll(
                    selector
                );

            for (const node of nodes) {
                if (isVisible(node)) {
                    return true;
                }
            }
        }

        return false;
    }

    // ============================================================
    // COMPLETED RESPONSE ACTION BAR
    // ============================================================

    function hasCompletedTurnActions(message) {
        if (!message || !message.isConnected) return false;

        // Only trust the CURRENT assistant's own action toolbar. In the Oct 8
        // ChatGPT layout it is the direct sibling of the content wrapper,
        // within the same assistant group container. Looking through distant
        // following siblings (old v1.4.1) found Copy on *previous* answers.
        let ancestor = message;
        for (let depth = 0; depth < 5 && ancestor; depth++) {
            for (const child of ancestor.children) {
                if (!child.matches || !child.matches('.turn-action-controls')) continue;
                if (!isVisible(child)) continue;

                // "Edit message" belongs to USER action bars and is NOT
                // sufficient proof that an assistant response has completed.
                const controls = child.querySelectorAll(
                    'button[aria-label="Copy"], ' +
                    'button[aria-label="Rate response"], ' +
                    'button[aria-label="Regenerate response"]'
                );
                if (Array.from(controls).some(isVisible)) return true;
            }
            ancestor = ancestor.parentElement;
        }
        return false;
    }

    // ============================================================
    // CLIPBOARD OUTPUT
    // ============================================================

    function writeBridgeClipboard(status, response = '', error = '') {
        // No PAD/clipboard transport in direct mode. Error UI is local and
        // the controller will retain its pending transaction for inspection.
        console.warn('[Direct Bridge] Local diagnostic:', status, currentHandoffId, error);
        return false;
    }

    function saveLastResult(result) {
        try {
            localStorage.setItem(
                'AG_BRIDGE_LAST_RESULT',
                JSON.stringify(
                    result
                )
            );
        } catch (_) {
            // Non-critical.
        }
    }

    // ============================================================
    // WATCH CLEANUP
    // ============================================================

    function stopSendWatch() {
        sendWatchActive = false;
        sendReadySince = 0;

        if (sendInterval) {
            clearInterval(
                sendInterval
            );

            sendInterval = null;
        }

        if (composerObserver) {
            composerObserver.disconnect();
            composerObserver = null;
        }

        cachedComposerForm = null;
    }

    function stopResponseWatch() {
        responseWatchActive = false;

        if (responseInterval) {
            clearInterval(
                responseInterval
            );

            responseInterval = null;
        }

        responseStableSince = 0;
        lastResponseText = '';
    }

    // ============================================================
    // FAILURE
    // ============================================================

    function failBridge(
        code,
        message
    ) {
        stopSendWatch();
        stopResponseWatch();

        writeBridgeClipboard(
            'ERROR',
            '',
            code
        );

        saveLastResult({
            bridge_handoff_id:
                currentHandoffId,

            status:
                'ERROR',

            copied_at:
                new Date().toISOString(),

            error:
                code,

            message:
                message
        });

        setBridgeState(
            'ERROR'
        );

        Object.assign(
            panel.style,
            {
                background:
                    'rgba(160,20,20,0.97)',

                border:
                    '3px solid white',

                fontWeight:
                    '700'
            }
        );

        showStatus(
            `❌ BRIDGE ERROR\n` +
            `${currentHandoffId || 'NO-ID'}\n` +
            `${message || code}`
        );

        hideStatusAfter(
            RESULT_POPUP_MS
        );
    }

    // ============================================================
    // RESPONSE FINISH
    // ============================================================

    async function finishResponse(assistantMessage) {
        if (directPosting) return;
        const text = getAssistantText(assistantMessage);
        if (!text || !directContext) {
            failBridge('EMPTY_OR_UNKNOWN_RESPONSE', 'No completed associated assistant response.');
            return;
        }
        stopResponseWatch();
        directPosting = true;
        setBridgeState('PUBLISHING');
        showStatus('↗ Publishing verified response\n' + currentHandoffId);
        try {
            const reply = await bridgeHttp('POST', '/response', {
                handoff_id: currentHandoffId,
                client_id: directClientId,
                request_sha256: directContext.request_sha256,
                response: text
            });
            if (reply.status !== 'ACCEPTED' || reply.handoff_id !== currentHandoffId) {
                throw new Error('Local server did not acknowledge matching response');
            }
            saveLastResult({
                bridge_handoff_id: currentHandoffId,
                status: 'DELIVERED',
                delivered_at: new Date().toISOString(),
                response_chars: text.length,
                response_sha256: reply.response_sha256
            });
            setBridgeState('DELIVERED');
            Object.assign(panel.style, { background: 'rgba(0,120,50,0.97)',
                border: '3px solid white', fontWeight: '700' });
            showStatus('✅ Direct bridge delivered\n' + currentHandoffId +
                       '\n' + text.length.toLocaleString() + ' chars\nPAD not used');
            directContext = null;
            hideStatusAfter(RESULT_POPUP_MS);
        } catch (e) {
            console.error('[Direct Bridge] Response rejected; not replaying:', e);
            setBridgeState('ERROR');
            Object.assign(panel.style, { background: 'rgba(160,20,20,0.97)',
                border: '3px solid white' });
            showStatus('❌ Response NOT accepted\n' + currentHandoffId +
                       '\n' + e.message + '\nInspect original transaction; no auto retry.');
            // Keep directContext and durable claim. Never send the response twice
            // without an evidence-based manual recovery.
        } finally {
            directPosting = false;
        }
    }

    // ============================================================
    // RESPONSE POLLING
    // ============================================================

    function pollResponse() {
        if (!responseWatchActive) return;

        const now = Date.now();
        if (now - responseStartedAt > RESPONSE_MAX_WAIT_MS) {
            failBridge('RESPONSE_TIMEOUT',
                'The new submitted turn was not confirmed complete; no old response was copied.');
            return;
        }

        // Never interpret an existing/re-rendered assistant message as the
        // answer to the current handoff. Require both a new user turn and a
        // later, previously unseen assistant turn.
        const assistantMessage = findNewAssistantMessage();
        if (!assistantMessage) {
            showStatus(
                `✅ Prompt sent\n${currentHandoffId}\n` +
                (acceptedUserId || acceptedUserNode
                    ? '🤖 New user turn confirmed; waiting for its assistant reply...'
                    : '⏳ Waiting for the new user turn to appear...'),
                '✕ Cancel Response Watch');
            return;
        }

        const candidateId = getAssistantIdentity(assistantMessage);
        if (assistantMessage !== responseCandidateNode || candidateId !== responseCandidateId) {
            responseCandidateNode = assistantMessage;
            responseCandidateId = candidateId;
            responseStableSince = 0;
            completedActionsSince = 0;
            lastResponseText = '';
        }

        const responseText = getAssistantText(assistantMessage);
        if (!responseText) {
            responseStableSince = 0;
            completedActionsSince = 0;
            showStatus(`🤖 New assistant reply appearing\n${currentHandoffId}`,
                '✕ Cancel Response Watch');
            return;
        }

        if (responseText !== lastResponseText) {
            lastResponseText = responseText;
            responseStableSince = now;
            completedActionsSince = 0;
            showStatus(`🤖 New ChatGPT reply streaming\n${currentHandoffId}\n` +
                `${responseText.length.toLocaleString()} chars`, '✕ Cancel Response Watch');
            return;
        }

        const connectionProblem = getChatGPTConnectionProblem();
        const generating = isChatGPTGenerating();
        const turnComplete = hasCompletedTurnActions(assistantMessage);

        // Fail CLOSED when end-of-turn evidence is unavailable. Unchanging
        // partial text is never sufficient to copy a response.
        if (connectionProblem && !turnComplete) {
            completedActionsSince = 0;
            showStatus(`⚠️ ChatGPT connection problem\n${currentHandoffId}\n` +
                `${connectionProblem}\nWaiting for recovery...`,
                '✕ Cancel Response Watch');
            return;
        }
        if (generating || !turnComplete) {
            completedActionsSince = 0;
            showStatus(`🤖 Waiting for the NEW response to finish\n${currentHandoffId}\n` +
                (generating ? 'Still generating...' : 'Waiting for its own Copy/Regenerate controls...'),
                '✕ Cancel Response Watch');
            return;
        }

        if (!completedActionsSince) completedActionsSince = now;
        const verifiedStableMs = now - Math.max(responseStableSince, completedActionsSince);
        if (verifiedStableMs < RESPONSE_STABLE_MS) {
            const remaining = Math.ceil((RESPONSE_STABLE_MS - verifiedStableMs) / 1000);
            showStatus(`✅ New response finished\n${currentHandoffId}\n` +
                `🔎 Confirming unchanged final text for ${remaining}s...`,
                '✕ Cancel Response Watch');
            return;
        }

        // Double-check all invariants immediately before writing clipboard.
        if (findNewAssistantMessage() !== assistantMessage ||
            isChatGPTGenerating() || !hasCompletedTurnActions(assistantMessage) ||
            getAssistantText(assistantMessage) !== responseText) {
            completedActionsSince = 0;
            return;
        }
        finishResponse(assistantMessage);
    }

    function startResponseWatch(baseline) {
        stopResponseWatch();

        baselineAssistantCount = baseline.count;
        baselineAssistantElement = baseline.latest;
        baselineAssistantText = baseline.text || '';
        baselineAssistantIdentity = baseline.identity || null;
        baselineAssistantIds = baseline.assistantIds;
        baselineAssistantNodes = baseline.assistantNodes;
        baselineUserIds = baseline.userIds;
        baselineUserNodes = baseline.userNodes;
        acceptedUserId = null;
        acceptedUserNode = null;
        responseCandidateId = null;
        responseCandidateNode = null;
        completedActionsSince = 0;
        lastResponseText = '';
        responseStableSince = 0;
        responseStartedAt = Date.now();
        responseWatchActive = true;

        setBridgeState('GENERATING');
        showStatus(`✅ Prompt sent\n${currentHandoffId}\n` +
            '⏳ Waiting for a NEW user turn and completed assistant reply...',
            '✕ Cancel Response Watch');
        responseInterval = setInterval(pollResponse, RESPONSE_POLL_MS);
    }

    // ============================================================
    // COMPOSER MUTATION OBSERVER
    // ============================================================

    function startComposerObserver() {
        if (composerObserver) {
            composerObserver.disconnect();
            composerObserver = null;
        }

        const composer =
            findComposer();

        if (!composer) {
            cachedComposerForm = null;
            return false;
        }

        const form =
            composer.closest(
                'form'
            );

        cachedComposerForm =
            form &&
            form.isConnected
                ? form
                : null;

        const target =
            cachedComposerForm ||
            composer;

        lastComposerMutationAt =
            Date.now();

        /*
         * IMPORTANT:
         *
         * Only reset the final send latch because we intentionally
         * reacquired/rebuilt the entire observer/form.
         *
         * Ordinary React mutations below DO NOT reset sendReadySince.
         */
        sendReadySince = 0;

        composerObserver =
            new MutationObserver(
                function () {
                    /*
                     * Track activity for the initial quiet-period check.
                     *
                     * DO NOT:
                     *     sendReadySince = 0;
                     *
                     * Once the final latch starts, harmless React
                     * mutations must not restart the countdown.
                     */
                    lastComposerMutationAt =
                        Date.now();
                }
            );

        /*
         * Do not monitor attributes because ChatGPT changes
         * presentation attributes frequently.
         */
        composerObserver.observe(
            target,
            {
                childList:
                    true,

                subtree:
                    true
            }
        );

        return true;
    }

    function refreshComposerObserverIfRequired() {
        const currentForm =
            getCurrentComposerForm();

        /*
         * React replaced the actual composer form.
         * This IS a meaningful change and should restart verification.
         */
        if (
            currentForm &&
            currentForm !==
                cachedComposerForm
        ) {
            startComposerObserver();
            return true;
        }

        if (
            cachedComposerForm &&
            !cachedComposerForm.isConnected
        ) {
            startComposerObserver();
            return true;
        }

        if (!composerObserver) {
            startComposerObserver();
            return true;
        }

        return false;
    }

    // ============================================================
    // SEND
    // ============================================================

    function sendNow() {
        /*
         * Reacquire the live Send button at the exact instant
         * we intend to click it.
         */
        const sendButton =
            findSendButton();

        if (
            !isSendReady(
                sendButton
            )
        ) {
            sendReadySince = 0;

            return false;
        }

        if (
            isComposerProcessing()
        ) {
            sendReadySince = 0;

            return false;
        }

        const baseline =
            captureAssistantBaseline();

        console.log(
            '[Autonomous Bridge] Sending:',
            currentHandoffId
        );

        /*
         * Stop the auto-send polling BEFORE the click so the
         * button can never be clicked twice by another poll.
         */
        stopSendWatch();

        if (directContext) {
            if (!composerContainsExactRequest(directContext.prompt)) {
                failBridge('REQUEST_CHANGED', 'Composer no longer matches the active request.');
                return false;
            }
            sessionStorage.setItem(DIRECT_SENT_KEY, currentHandoffId);
        }
        sendButton.click();

        startResponseWatch(
            baseline
        );

        return true;
    }

    // ============================================================
    // AUTO-SEND POLLING
    // ============================================================

    function pollSendReadiness() {
        if (!sendWatchActive) {
            return;
        }

        const now =
            Date.now();

        const elapsed =
            now -
            pasteStartedAt;

        const elapsedSeconds =
            Math.floor(
                elapsed /
                1000
            );

        if (
            elapsed >
            SEND_MAX_WAIT_MS
        ) {
            failBridge(
                'PASTE_READY_TIMEOUT',
                'ChatGPT composer never became ready to send.'
            );

            return;
        }

        const minimumWaitMs =
            MIN_WAIT_SECONDS *
            1000;

        // --------------------------------------------------------
        // STEP 1 — mandatory minimum wait
        // --------------------------------------------------------

        if (
            elapsed <
            minimumWaitMs
        ) {
            const remaining =
                Math.ceil(
                    (
                        minimumWaitMs -
                        elapsed
                    ) /
                    1000
                );

            showStatus(
                `📋 Bridge paste detected\n` +
                `${currentHandoffId}\n` +
                `${pasteLength.toLocaleString()} chars\n` +
                `⏳ Minimum wait: ${remaining}s`,
                '✕ Cancel Auto-Send'
            );

            sendReadySince = 0;

            return;
        }

        // --------------------------------------------------------
        // STEP 2 — make sure we still point at the live composer
        // --------------------------------------------------------

        if (
            refreshComposerObserverIfRequired()
        ) {
            showStatus(
                `🔄 ${elapsedSeconds}s — reacquiring live composer...`,
                '✕ Cancel Auto-Send'
            );

            return;
        }

        // --------------------------------------------------------
        // STEP 3 — live Send button must still be ready
        // --------------------------------------------------------

        const sendButton =
            findSendButton();

        if (
            !isSendReady(
                sendButton
            )
        ) {
            showStatus(
                `⏳ ${elapsedSeconds}s — waiting for ChatGPT Send button...`,
                '✕ Cancel Auto-Send'
            );

            /*
             * This IS a meaningful loss of readiness.
             */
            sendReadySince = 0;

            return;
        }

        // --------------------------------------------------------
        // STEP 4 — attachment/paste processing must be finished
        // --------------------------------------------------------

        if (
            isComposerProcessing()
        ) {
            showStatus(
                `📎 ${elapsedSeconds}s — pasted attachment still processing...`,
                '✕ Cancel Auto-Send'
            );

            /*
             * This IS a meaningful loss of readiness.
             */
            sendReadySince = 0;

            return;
        }

        // --------------------------------------------------------
        // STEP 5 — before latch begins, require initial quiet period
        // --------------------------------------------------------

        if (!sendReadySince) {
            const quietFor =
                now -
                lastComposerMutationAt;

            if (
                quietFor <
                DOM_QUIET_MS
            ) {
                showStatus(
                    `🔄 ${elapsedSeconds}s — composer still settling...`,
                    '✕ Cancel Auto-Send'
                );

                return;
            }

            /*
             * LATCH READY.
             *
             * From this point onward harmless React DOM mutations
             * DO NOT restart the countdown.
             *
             * Only:
             *   - Send becoming unavailable,
             *   - attachment processing restarting,
             *   - or the entire composer form being replaced
             * can reset this.
             */
            sendReadySince =
                now;

            showStatus(
                `✅ Composer ready\n` +
                `${currentHandoffId}\n` +
                `🔎 Final verification...`,
                '✕ Cancel Auto-Send'
            );

            return;
        }

        // --------------------------------------------------------
        // STEP 6 — final latched countdown
        // --------------------------------------------------------

        const stableFor =
            now -
            sendReadySince;

        if (
            stableFor >=
            READY_STABLE_MS
        ) {
            const sent =
                sendNow();

            if (!sent) {
                showStatus(
                    `⏳ ${elapsedSeconds}s — Send changed during final check; retrying...`,
                    '✕ Cancel Auto-Send'
                );
            }

            return;
        }

        const remaining =
            Math.max(
                1,
                Math.ceil(
                    (
                        READY_STABLE_MS -
                        stableFor
                    ) /
                    1000
                )
            );

        showStatus(
            `✅ Ready — sending in ${remaining}s`,
            '✕ Cancel Auto-Send'
        );
    }

    // ============================================================
    // START BRIDGE PASTE WATCH
    // ============================================================

    function startBridgePaste(
        text
    ) {
        stopSendWatch();
        stopResponseWatch();

        resetPanelStyle();

        currentHandoffId =
            extractHandoffId(
                text
            );

        if (!currentHandoffId) {
            return;
        }

        pasteStartedAt =
            Date.now();

        pasteLength =
            text.length;

        sendReadySince =
            0;

        lastComposerMutationAt =
            Date.now();

        sendWatchActive =
            true;

        setBridgeState(
            'WAITING'
        );

        showStatus(
            `📋 Bridge paste detected\n` +
            `${currentHandoffId}\n` +
            `${text.length.toLocaleString()} chars\n` +
            `⏳ Waiting at least ${MIN_WAIT_SECONDS}s`,
            '✕ Cancel Auto-Send'
        );

        /*
         * Give ChatGPT a moment to perform native paste handling,
         * including conversion to a "Pasted text..." attachment.
         */
        setTimeout(
            function () {
                if (
                    sendWatchActive
                ) {
                    startComposerObserver();
                }
            },
            100
        );

        sendInterval =
            setInterval(
                pollSendReadiness,
                SEND_POLL_MS
            );
    }

    // ============================================================
    // PASTE EVENT
    // ============================================================

    if (!DIRECT_MODE) document.addEventListener(
        'paste',
        function (event) {
            const composer =
                findComposer();

            if (!composer) {
                return;
            }

            if (
                event.target !==
                    composer &&
                !composer.contains(
                    event.target
                )
            ) {
                return;
            }

            let text = '';

            try {
                text =
                    event.clipboardData
                        ?.getData(
                            'text/plain'
                        ) ||
                    '';
            } catch (_) {
                return;
            }

            if (!text) {
                return;
            }

            const handoffId =
                extractHandoffId(
                    text
                );

            console.log(
                '[Autonomous Bridge] Paste:',
                text.length,
                'chars; bridge:',
                handoffId
            );

            /*
             * Only genuine HND bridge prompts are eligible
             * for unattended auto-send.
             */
            if (!handoffId) {
                return;
            }

            /*
             * IMPORTANT:
             *
             * Do NOT preventDefault().
             *
             * ChatGPT needs to process the paste normally.
             */
            startBridgePaste(
                text
            );
        },
        true
    );

    // ============================================================
    // CANCEL BUTTON
    // ============================================================

    cancelButton.addEventListener(
        'click',
        function () {
            if (
                sendWatchActive
            ) {
                stopSendWatch();

                failBridge(
                    'AUTO_SEND_CANCELLED',
                    'Auto-send cancelled by user.'
                );

                return;
            }

            if (
                responseWatchActive
            ) {
                stopResponseWatch();

                failBridge(
                    'RESPONSE_WATCH_CANCELLED',
                    'Response watch cancelled by user.'
                );
            }
        }
    );

    // ============================================================
    // BLOCK ENTER WHILE AUTO-SEND IS ARMED
    // ============================================================

    document.addEventListener(
        'keydown',
        function (event) {
            if (
                !sendWatchActive
            ) {
                return;
            }

            const composer =
                findComposer();

            if (!composer) {
                return;
            }

            if (
                event.target !==
                    composer &&
                !composer.contains(
                    event.target
                )
            ) {
                return;
            }

            if (
                event.key ===
                    'Enter' &&
                !event.shiftKey
            ) {
                event.preventDefault();
                event.stopPropagation();
                event.stopImmediatePropagation();

                showStatus(
                    `🛑 Enter blocked\n` +
                    `${currentHandoffId}\n` +
                    `Bridge auto-send is armed.`,
                    '✕ Cancel Auto-Send'
                );
            }
        },
        true
    );

    // ============================================================
    // ESCAPE CANCEL
    // ============================================================

    document.addEventListener(
        'keydown',
        function (event) {
            if (
                event.key !==
                'Escape'
            ) {
                return;
            }

            if (
                sendWatchActive
            ) {
                stopSendWatch();

                failBridge(
                    'AUTO_SEND_CANCELLED',
                    'Auto-send cancelled with Escape.'
                );

                return;
            }

            if (
                responseWatchActive
            ) {
                stopResponseWatch();

                failBridge(
                    'RESPONSE_WATCH_CANCELLED',
                    'Response watch cancelled with Escape.'
                );
            }
        },
        true
    );

    // ============================================================
    // STARTUP
    // ============================================================

    setBridgeState(
        'IDLE'
    );

    setInterval(pollDirectBridge, DIRECT_POLL_MS);
    pollDirectBridge();
    console.log('[ChatGPT Direct Local Bridge] v2.0.0 loaded; PAD disabled.');

})();
