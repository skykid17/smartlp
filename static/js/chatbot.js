/**
 * Chatbot Module - ES6
 * Manages the chatbot modal and interactions
 */

class Chatbot {
    constructor() {
        this.modal = document.getElementById('chatbotModal');
        this.messagesContainer = document.getElementById('chatMessages');
        this.input = document.getElementById('chatInput');
        this.sendBtn = document.getElementById('chatSend');

        this.session = [];
        this.MAX_HISTORY_TURNS = 20; // Keep last 20 messages to avoid context overflow

        this.init();
    }

    init() {
        this.sendBtn?.addEventListener('click', () => this.sendMessage());
        this.input?.addEventListener('keypress', (e) => e.key === 'Enter' && this.sendMessage());
        this.modal?.addEventListener('click', (e) => e.target === this.modal && this.close());
    }

    open() {
        this.modal.classList.remove('hidden');
        this.input?.focus();
    }

    close() {
        this.modal.classList.add('hidden');
    }

    sendMessage() {
        const message = this.input?.value.trim();
        if (!message) return;

        this.addMessage(message, 'user');
        this.session.push({ role: 'user', content: message });
        this.input.value = '';
        this.getResponse();
    }

    buildPrompt() {
        const recent = this.session.slice(-this.MAX_HISTORY_TURNS);
        return recent
            .map(m => `${m.role === 'user' ? 'User' : 'Assistant'}: ${m.content}`)
            .join('\n');
    }


    addMessage(text, sender = 'bot') {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'flex items-start space-x-3';

        if (sender === 'user') {
            messageDiv.className += ' flex-row-reverse space-x-reverse';
            messageDiv.innerHTML = `
                <div class="flex-shrink-0 w-8 h-8 bg-gray-300 dark:bg-gray-600 rounded-full flex items-center justify-center">
                    <i class="fas fa-user text-gray-700 dark:text-gray-300 text-sm"></i>
                </div>
                <div class="bg-blue-500 text-white rounded-lg px-4 py-2 max-w-[60%] break-words">
                    <p class="text-sm whitespace-pre-wrap">${this.escapeHtml(text)}</p>
                </div>
            `;
        } else {
            // Render bot messages as markdown-aware HTML
            const rendered = this.renderMarkdown(text);
            messageDiv.innerHTML = `
                <div class="flex-shrink-0 w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                    <i class="fas fa-robot text-white text-sm"></i>
                </div>
                <div class="flex flex-col">
                    <div class="bg-gray-100 dark:bg-gray-700 rounded-lg px-4 py-2 markdown-message text-gray-900 dark:text-white break-words max-w-[70%]">${rendered}</div>
                    <div class="flex justify-end mt-1">
                        <button type="button" class="copy-reply inline-flex items-center space-x-2 text-gray-500 hover:text-gray-700 text-sm px-2 py-1 rounded" data-raw="${this.escapeAttr(text)}" aria-label="Copy reply">
                            <i class="fas fa-copy"></i>
                        </button>
                    </div>
                </div>
            `;
        }

        this.messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();

        // Attach copy handler for the new button if present
        const copyBtn = messageDiv.querySelector('.copy-reply');
        if (copyBtn) {
            copyBtn.addEventListener('click', async (e) => {
                try {
                    const raw = copyBtn.getAttribute('data-raw') || '';
                    await navigator.clipboard.writeText(raw);
                    if (window.showToast) window.showToast('Reply copied', 'info');
                } catch (err) {
                    if (window.showToast) window.showToast('Copy failed', 'error');
                }
            });
        }
    }


    async getResponse() {
        this.showTyping();

        try {
            const prompt = this.buildPrompt();

            const response = await fetch('/api/query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    task: 'chat',
                    prompt: prompt
                })
            });

            const data = await response.json();
            this.removeTyping();

            if (data.success && data.content) {
                this.addMessage(data.content, 'bot');

                // Save assistant reply
                this.session.push({
                    role: 'assistant',
                    content: data.content
                });
            } else {
                this.addMessage('Sorry, I encountered an error.', 'bot');
            }

        } catch (error) {
            console.error('Chatbot error:', error);
            this.removeTyping();
            this.addMessage('Connection issue. Please try again later.', 'bot');
        }
    }


    showTyping() {
        const typingDiv = document.createElement('div');
        typingDiv.id = 'typing-indicator';
        typingDiv.className = 'flex items-start space-x-3';
        typingDiv.innerHTML = `
            <div class="flex-shrink-0 w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                <i class="fas fa-robot text-white text-sm"></i>
            </div>
            <div class="bg-gray-100 dark:bg-gray-700 rounded-lg p-3">
                <div class="flex space-x-1">
                    <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0s"></div>
                    <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
                    <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.4s"></div>
                </div>
            </div>
        `;
        this.messagesContainer.appendChild(typingDiv);
        this.scrollToBottom();
    }

    removeTyping() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    scrollToBottom() {
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }

    escapeAttr(s) {
        if (!s) return '';
        return String(s).replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }

    renderMarkdown(text) {
        if (!text) return '';

        // If a markdown library is present, prefer it (safe fallback: simple renderer below)
        if (window.marked && typeof window.marked.parse === 'function') {
            try {
                return window.marked.parse(text);
            } catch (e) {
                // fall through to builtin renderer
            }
        }

        // Basic safe renderer:
        // 1) escape HTML, 2) extract code blocks, 3) convert links, code, emphasis, lists, paragraphs
        let escaped = this.escapeHtml(text);

        const codeBlocks = [];
        escaped = escaped.replace(/```([\s\S]*?)```/g, function (_, code) {
            codeBlocks.push('<pre><code>' + code + '</code></pre>');
            return '@@CODEBLOCK' + (codeBlocks.length - 1) + '@@';
        });

        // Links
        escaped = escaped.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (m, label, url) => {
            return `<a href="${this.escapeAttr(url)}" target="_blank" rel="noopener noreferrer">${label}</a>`;
        });

        // Inline code
        escaped = escaped.replace(/`([^`]+)`/g, (m, code) => `<code>${code}</code>`);

        // Bold and italic
        escaped = escaped.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
        escaped = escaped.replace(/__(.+?)__/g, '<strong>$1</strong>');
        escaped = escaped.replace(/\*(?!\*)([^*]+)\*/g, '<em>$1</em>');
        escaped = escaped.replace(/_(?!_)([^_]+)_/g, '<em>$1</em>');

        // Simple unordered lists
        const lines = escaped.split('\n');
        const out = [];
        let inList = false;
        for (let i = 0; i < lines.length; i++) {
            const line = lines[i];
            const m = line.match(/^\s*[-*]\s+(.*)/);
            if (m) {
                if (!inList) { out.push('<ul>'); inList = true; }
                out.push('<li>' + m[1] + '</li>');
            } else {
                if (inList) { out.push('</ul>'); inList = false; }
                out.push(line);
            }
        }
        if (inList) out.push('</ul>');

        let withLists = out.join('\n');

        // Paragraphs: double newlines -> paragraphs, single newline -> <br>
        const paragraphs = withLists.split(/\n\s*\n/).map(p => '<p>' + p.replace(/\n/g, '<br>') + '</p>');
        let result = paragraphs.join('');

        // Restore code blocks
        result = result.replace(/@@CODEBLOCK(\d+)@@/g, (m, idx) => codeBlocks[Number(idx)] || '');

        // Sanitize output if DOMPurify is available
        if (window.DOMPurify && typeof window.DOMPurify.sanitize === 'function') {
            try {
                return window.DOMPurify.sanitize(result);
            } catch (e) {
                // fallback to raw result
            }
        }

        return result;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize
const chatbot = new Chatbot();

// Make available globally
window.chatbot = chatbot;

export default chatbot;
