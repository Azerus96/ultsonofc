class GameAnimations {
    constructor() {
        this.animationQueue = [];
        this.isAnimating = false;
    }

    async showScoreAnimation(position, score, isWin) {
        const element = document.createElement('div');
        element.className = `score-animation ${isWin ? 'win' : 'lose'}`;
        element.textContent = isWin ? `+${score}` : `-${score}`;

        const container = document.querySelector(`#${position}-row`);
        container.appendChild(element);

        await this.animate(element, [
            { opacity: 0, transform: 'translateY(0) scale(0.8)' },
            { opacity: 1, transform: 'translateY(-20px) scale(1.2)' },
            { opacity: 0, transform: 'translateY(-40px) scale(0.8)' }
        ], {
            duration: 1500,
            easing: 'ease-out'
        });

        element.remove();
    }

    async showFantasyAnimation() {
        const overlay = document.createElement('div');
        overlay.className = 'fantasy-overlay';
        document.body.appendChild(overlay);

        const text = document.createElement('div');
        text.className = 'fantasy-text';
        text.textContent = 'ФАНТАЗИЯ!';
        overlay.appendChild(text);

        await this.animate(overlay, [
            { opacity: 0 },
            { opacity: 0.7 },
            { opacity: 0 }
        ], {
            duration: 2000,
            easing: 'ease-in-out'
        });

        overlay.remove();
    }

    async showCardPlacement(card, fromPosition, toPosition) {
        const cardElement = document.createElement('div');
        cardElement.className = 'card animated';
        cardElement.textContent = `${card.rank}${card.suit}`;
        cardElement.dataset.suit = card.suit;

        const startRect = fromPosition.getBoundingClientRect();
        const endRect = toPosition.getBoundingClientRect();

        cardElement.style.position = 'fixed';
        cardElement.style.left = `${startRect.left}px`;
        cardElement.style.top = `${startRect.top}px`;
        document.body.appendChild(cardElement);

        await this.animate(cardElement, [
            { 
                transform: 'scale(1) rotate(0deg)',
                left: `${startRect.left}px`,
                top: `${startRect.top}px`
            },
            { 
                transform: 'scale(1.1) rotate(180deg)',
                left: `${(startRect.left + endRect.left) / 2}px`,
                top: `${(startRect.top + endRect.top) / 2}px`
            },
            { 
                transform: 'scale(1) rotate(360deg)',
                left: `${endRect.left}px`,
                top: `${endRect.top}px`
            }
        ], {
            duration: 600,
            easing: 'ease-in-out'
        });

        cardElement.remove();
    }

    async showCombinationAnimation(position, combination) {
        const container = document.querySelector(`#${position}-row`);
        const highlight = document.createElement('div');
        highlight.className = 'combination-highlight';
        container.appendChild(highlight);

        const text = document.createElement('div');
        text.className = 'combination-text';
        text.textContent = combination;
        highlight.appendChild(text);

        await this.animate(highlight, [
            { opacity: 0, transform: 'scale(0.8)' },
            { opacity: 1, transform: 'scale(1)' },
            { opacity: 1, transform: 'scale(1)' },
            { opacity: 0, transform: 'scale(0.8)' }
        ], {
            duration: 2000,
            easing: 'ease-in-out'
        });

        highlight.remove();
    }

    async animate(element, keyframes, options) {
        return new Promise(resolve => {
            const animation = element.animate(keyframes, options);
            animation.onfinish = resolve;
        });
    }

    queueAnimation(animationFunction) {
        return new Promise(async (resolve) => {
            this.animationQueue.push({ func: animationFunction, resolve });
            if (!this.isAnimating) {
                this.processAnimationQueue();
            }
        });
    }

    async processAnimationQueue() {
        if (this.animationQueue.length === 0) {
            this.isAnimating = false;
            return;
        }

        this.isAnimating = true;
        const { func, resolve } = this.animationQueue.shift();
        await func();
        resolve();
        this.processAnimationQueue();
    }
}

// UI компоненты
class GameUI {
    constructor(animations) {
        this.animations = animations;
        this.setupUI();
    }

    setupUI() {
        this.setupTooltips();
        this.setupModals();
        this.setupChat();
    }

    setupTooltips() {
        const tooltips = document.querySelectorAll('[data-tooltip]');
        tooltips.forEach(element => {
            element.addEventListener('mouseenter', (e) => {
                const tooltip = document.createElement('div');
                tooltip.className = 'tooltip';
                tooltip.textContent = element.dataset.tooltip;
                document.body.appendChild(tooltip);

                const rect = element.getBoundingClientRect();
                tooltip.style.left = `${rect.left + rect.width / 2 - tooltip.offsetWidth / 2}px`;
                tooltip.style.top = `${rect.top - tooltip.offsetHeight - 10}px`;

                element.addEventListener('mouseleave', () => tooltip.remove(), { once: true });
            });
        });
    }

    setupModals() {
        const modals = document.querySelectorAll('.modal');
        const modalTriggers = document.querySelectorAll('[data-modal]');

        modalTriggers.forEach(trigger => {
            trigger.addEventListener('click', () => {
                const modalId = trigger.dataset.modal;
                const modal = document.querySelector(`#${modalId}`);
                if (modal) {
                    modal.classList.add('active');
                }
            });
        });

        modals.forEach(modal => {
            const closeBtn = modal.querySelector('.modal-close');
            if (closeBtn) {
                closeBtn.addEventListener('click', () => {
                    modal.classList.remove('active');
                });
            }

            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.classList.remove('active');
                }
            });
        });
    }

    setupChat() {
        const chatInput = document.querySelector('#chat-input');
        const chatForm = document.querySelector('#chat-form');

        chatForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const message = chatInput.value.trim();
            if (message) {
                // Отправка сообщения обрабатывается в GameClient
                window.gameClient.sendChatMessage(message);
                chatInput.value = '';
            }
        });
    }

    showError(message) {
        const errorElement = document.createElement('div');
        errorElement.className = 'error-message';
        errorElement.textContent = message;
        document.body.appendChild(errorElement);

        setTimeout(() => {
            errorElement.remove();
        }, 3000);
    }

    updateGameStatus(status) {
        const statusElement = document.querySelector('#game-status');
        statusElement.textContent = status;
    }
}

// Экспорт классов
window.GameAnimations = GameAnimations;
window.GameUI = GameUI;
