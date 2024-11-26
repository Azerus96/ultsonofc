class GameClient {
    constructor() {
        this.socket = io();
        this.playerId = null;
        this.gameState = null;
        this.setupSocketHandlers();
        this.setupEventListeners();
    }

    setupSocketHandlers() {
        this.socket.on('connect', () => {
            console.log('Connected to server');
        });

        this.socket.on('game_state', (state) => {
            this.gameState = state;
            this.updateUI();
        });

        this.socket.on('error', (data) => {
            alert(data.message);
        });

        this.socket.on('chat_message', (data) => {
            this.addChatMessage(data);
        });
    }

    setupEventListeners() {
        // Обработчики для drag and drop
        document.querySelectorAll('.card').forEach(card => {
            card.addEventListener('dragstart', this.handleDragStart.bind(this));
            card.addEventListener('dragend', this.handleDragEnd.bind(this));
        });

        document.querySelectorAll('.card-slot').forEach(slot => {
            slot.addEventListener('dragover', this.handleDragOver.bind(this));
            slot.addEventListener('drop', this.handleDrop.bind(this));
        });

        // Обработчик готовности
        document.getElementById('ready-btn').addEventListener('click', () => {
            this.socket.emit('player_ready', { player_id: this.playerId });
        });
    }

    handleDragStart(e) {
        if (!this.canMove()) return;
        
        const card = e.target;
        card.classList.add('dragging');
        e.dataTransfer.setData('text/plain', JSON.stringify({
            rank: card.dataset.rank,
            suit: card.dataset.suit
        }));
    }

    handleDragEnd(e) {
        e.target.classList.remove('dragging');
    }

    handleDragOver(e) {
        e.preventDefault();
        if (this.canMove()) {
            e.target.classList.add('drag-over');
        }
    }

    handleDrop(e) {
        e.preventDefault();
        if (!this.canMove()) return;

        const slot = e.target.closest('.card-slot');
        const cardData = JSON.parse(e.dataTransfer.getData('text/plain'));
        
        this.socket.emit('place_card', {
            player_id: this.playerId,
            card: cardData,
            position: slot.dataset.position,
            index: Array.from(slot.parentNode.children).indexOf(slot)
        });

        slot.classList.remove('drag-over');
    }

    canMove() {
        return this.gameState && 
               this.gameState.current_player === this.playerId &&
               ['playing', 'fantasy'].includes(this.gameState.state);
    }

    updateUI() {
        this.updateHand();
        this.updateTable();
        this.updateScores();
        this.updateGameStatus();
        this.updateTimer();
    }

    updateHand() {
        const hand = document.getElementById('hand');
        const player = this.gameState.players[this.playerId];
        
        if (!player) return;

        hand.innerHTML = '';
        player.hand.current.forEach(card => {
            const cardElement = this.createCardElement(card);
            hand.appendChild(cardElement);
        });
    }

    updateTable() {
        const positions = ['top', 'middle', 'bottom'];
        const player = this.gameState.players[this.playerId];
        
        if (!player) return;

        positions.forEach(position => {
            const row = document.getElementById(`${position}-row`);
            row.innerHTML = '';
            
            // Создаем слоты
            const maxSlots = position === 'top' ? 3 : 5;
            for (let i = 0; i < maxSlots; i++) {
                const slot = document.createElement('div');
                slot.className = 'card-slot';
                slot.dataset.position = position;
                
                // Если в слоте есть карта, добавляем её
                const card = player.hand[position][i];
                if (card) {
                    slot.appendChild(this.createCardElement(card));
                }
                
                row.appendChild(slot);
            }
        });

        // Обновляем стол оппонента, если он есть
        if (this.gameState.opponent_table) {
            this.updateOpponentTable();
        }
    }

    updateOpponentTable() {
        const positions = ['top', 'middle', 'bottom'];
        const opponentId = Object.keys(this.gameState.players)
            .find(id => id !== this.playerId);
        
        if (!opponentId) return;
        
        const opponent = this.gameState.players[opponentId];
        
        positions.forEach(position => {
            const row = document.getElementById(`opponent-${position}-row`);
            row.innerHTML = '';
            
            const maxSlots = position === 'top' ? 3 : 5;
            for (let i = 0; i < maxSlots; i++) {
                const slot = document.createElement('div');
                slot.className = 'card-slot';
                
                const card = opponent.hand[position][i];
                if (card) {
                    slot.appendChild(this.createCardElement(card, true));
                }
                
                row.appendChild(slot);
            }
        });
    }

    createCardElement(card, isOpponent = false) {
        const cardElement = document.createElement('div');
        cardElement.className = 'card';
        cardElement.dataset.suit = card.suit;
        cardElement.dataset.rank = card.rank;
        cardElement.textContent = `${card.rank}${card.suit}`;
        
        if (!isOpponent) {
            cardElement.draggable = true;
        }
        
        return cardElement;
    }

    updateScores() {
        const scoreBoard = document.getElementById('score-board');
        scoreBoard.innerHTML = '';
        
        Object.entries(this.gameState.players).forEach(([id, player]) => {
            const scoreElement = document.createElement('div');
            scoreElement.className = 'player-score';
            scoreElement.innerHTML = `
                <span class="player-name">${player.name}</span>
                <span class="score">${player.score}</span>
            `;
            scoreBoard.appendChild(scoreElement);
        });
    }

    updateGameStatus() {
        const statusElement = document.getElementById('game-status');
        const readyButton = document.getElementById('ready-btn');
        
        let statusText = '';
        switch (this.gameState.state) {
            case 'waiting':
                statusText = 'Ожидание игроков...';
                readyButton.style.display = 'block';
                break;
            case 'playing':
                statusText = `Улица ${this.gameState.current_street}`;
                readyButton.style.display = 'none';
                break;
            case 'fantasy':
                statusText = 'Фантазия!';
                break;
            case 'scoring':
                statusText = 'Подсчет очков...';
                break;
            case 'finished':
                statusText = 'Игра завершена';
                break;
        }
        
        statusElement.textContent = statusText;
    }

    updateTimer() {
        const timerElement = document.getElementById('timer');
        const player = this.gameState.players[this.playerId];
        
        if (player && this.canMove()) {
            timerElement.textContent = `Время: ${player.time_bank}с`;
            timerElement.style.display = 'block';
        } else {
            timerElement.style.display = 'none';
        }
    }

    addChatMessage(data) {
        const chatBox = document.getElementById('chat-box');
        const messageElement = document.createElement('div');
        messageElement.className = 'chat-message';
        messageElement.innerHTML = `
            <span class="player-name">${data.player_name}:</span>
            <span class="message">${data.message}</span>
        `;
        chatBox.appendChild(messageElement);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    sendChatMessage(message) {
        this.socket.emit('chat_message', {
            player_id: this.playerId,
            message: message
        });
    }

    init(playerId) {
        this.playerId = playerId;
        this.setupEventListeners();
        this.socket.emit('join_game', { player_id: playerId });
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    const gameClient = new GameClient();
    const playerId = document.body.dataset.playerId;
    gameClient.init(playerId);
});
