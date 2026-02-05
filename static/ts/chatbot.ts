/**
 * Tourwise Chatbot Interface
 * Clean, minimal chat interface inspired by modern AI chat applications
 */

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

class TourwiseChatbot {
  private chatInput: HTMLTextAreaElement;
  private sendBtn: HTMLButtonElement;
  private welcomeSection: HTMLElement;
  private messagesContainer: HTMLElement;
  private messages: ChatMessage[] = [];

  constructor() {
    this.chatInput = document.getElementById('chatInput') as HTMLTextAreaElement;
    this.sendBtn = document.getElementById('sendBtn') as HTMLButtonElement;
    this.welcomeSection = document.getElementById('welcomeSection') as HTMLElement;
    this.messagesContainer = document.getElementById('messagesContainer') as HTMLElement;

    this.init();
  }

  private init(): void {
    // Auto-resize textarea
    this.chatInput.addEventListener('input', () => this.handleInputChange());
    
    // Handle send button click
    this.sendBtn.addEventListener('click', () => this.sendMessage());
    
    // Handle Enter key (Shift+Enter for new line)
    this.chatInput.addEventListener('keydown', (e: KeyboardEvent) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.sendMessage();
      }
    });

    // Focus input on load
    this.chatInput.focus();
  }

  private handleInputChange(): void {
    const value = this.chatInput.value.trim();
    
    // Enable/disable send button
    this.sendBtn.disabled = value.length === 0;
    
    // Auto-resize textarea
    this.chatInput.style.height = 'auto';
    this.chatInput.style.height = Math.min(this.chatInput.scrollHeight, 200) + 'px';
  }

  private sendMessage(): void {
    const content = this.chatInput.value.trim();
    
    if (!content) return;

    // Create user message
    const userMessage: ChatMessage = {
      role: 'user',
      content,
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
  }

  private renderMessage(message: ChatMessage): void {
    const messageEl = document.createElement('div');
    messageEl.className = `message message-${message.role}`;
    
    const contentEl = document.createElement('div');
    contentEl.className = 'message-content';
    contentEl.textContent = message.content;
    
    messageEl.appendChild(contentEl);
    this.messagesContainer.appendChild(messageEl);
  }

  private scrollToBottom(): void {
    this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
  }
}

// Initialize chatbot when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  new TourwiseChatbot();
});
