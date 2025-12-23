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
        
        this.init();
    }

    init() {
        // Send button click
        this.sendBtn?.addEventListener('click', () => {
            this.sendMessage();
        });

        // Enter key to send
        this.input?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });

        // Close modal on outside click
        this.modal?.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.close();
            }
        });
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

        // Add user message
        this.addMessage(message, 'user');
        
        // Clear input
        this.input.value = '';

        // Send to backend and get response
        this.getResponse(message);
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
                <div class="bg-blue-500 text-white rounded-lg p-3 max-w-md">
                    <p class="text-sm">${this.escapeHtml(text)}</p>
                </div>
            `;
        } else {
            messageDiv.innerHTML = `
                <div class="flex-shrink-0 w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                    <i class="fas fa-robot text-white text-sm"></i>
                </div>
                <div class="bg-gray-100 dark:bg-gray-700 rounded-lg p-3 max-w-md">
                    <p class="text-sm text-gray-900 dark:text-white">${this.escapeHtml(text)}</p>
                </div>
            `;
        }

        this.messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }

    async getResponse(message) {
        // Show typing indicator
        this.showTyping();

        try {
            const response = await fetch('/api/chatbot', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message })
            });

            const data = await response.json();
            
            // Remove typing indicator
            this.removeTyping();

            if (data.response) {
                this.addMessage(data.response, 'bot');
            } else {
                this.addMessage('Sorry, I encountered an error. Please try again.', 'bot');
            }
        } catch (error) {
            console.error('Chatbot error:', error);
            this.removeTyping();
            this.addMessage('I\'m having trouble connecting right now. Please try again later.', 'bot');
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
