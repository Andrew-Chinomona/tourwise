/**
 * Tourwise Chatbot Interface
 * Clean, minimal chat interface inspired by modern AI chat applications
 */
"use strict";
var TourwiseChatbot = /** @class */ (function () {
    function TourwiseChatbot() {
        this.messages = [];
        this.chatInput = document.getElementById('chatInput');
        this.sendBtn = document.getElementById('sendBtn');
        this.welcomeSection = document.getElementById('welcomeSection');
        this.messagesContainer = document.getElementById('messagesContainer');
        this.init();
    }
    TourwiseChatbot.prototype.init = function () {
        var _this = this;
        // Auto-resize textarea
        this.chatInput.addEventListener('input', function () { return _this.handleInputChange(); });
        // Handle send button click
        this.sendBtn.addEventListener('click', function () { return _this.sendMessage(); });
        // Handle Enter key (Shift+Enter for new line)
        this.chatInput.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                _this.sendMessage();
            }
        });
        // Focus input on load
        this.chatInput.focus();
    };
    TourwiseChatbot.prototype.handleInputChange = function () {
        var value = this.chatInput.value.trim();
        // Enable/disable send button
        this.sendBtn.disabled = value.length === 0;
        // Auto-resize textarea
        this.chatInput.style.height = 'auto';
        this.chatInput.style.height = Math.min(this.chatInput.scrollHeight, 200) + 'px';
    };
    TourwiseChatbot.prototype.sendMessage = function () {
        var content = this.chatInput.value.trim();
        if (!content)
            return;
        // Create user message
        var userMessage = {
            role: 'user',
            content: content,
            timestamp: new Date()
        };
        this.messages.push(userMessage);
        // Hide welcome section, show messages
        this.welcomeSection.style.display = 'none';
        this.messagesContainer.classList.add('active');
        // Render user message
        this.renderMessage(userMessage);
        // Clear input
        this.chatInput.value = '';
        this.handleInputChange();
        // Scroll to bottom
        this.scrollToBottom();
    };
    TourwiseChatbot.prototype.renderMessage = function (message) {
        var messageEl = document.createElement('div');
        messageEl.className = "message message-" + message.role;
        var contentEl = document.createElement('div');
        contentEl.className = 'message-content';
        contentEl.textContent = message.content;
        messageEl.appendChild(contentEl);
        this.messagesContainer.appendChild(messageEl);
    };
    TourwiseChatbot.prototype.scrollToBottom = function () {
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    };
    return TourwiseChatbot;
}());
// Initialize chatbot when DOM is ready
document.addEventListener('DOMContentLoaded', function () {
    new TourwiseChatbot();
});
