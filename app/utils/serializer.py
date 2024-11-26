import os
import json
import base64
from datetime import datetime
from github import Github
from typing import Dict, Optional

class ProgressSerializer:
    def __init__(self, player_id: str, token: Optional[str] = None):
        self.token = token or os.environ.get('AI_PROGRESS_TOKEN')
        if not self.token:
            raise ValueError("AI_PROGRESS_TOKEN not found in environment variables")
            
        self.github = Github(self.token)
        self.player_id = player_id
        # Используем ваш GitHub username и название репозитория
        self.repo = self.github.get_repo("Azerus96/ultsonofc")

    def save_progress(self, state: Dict) -> bool:
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"progress/{self.player_id}_{timestamp}.json"
            
            # Конвертируем состояние в JSON
            content = json.dumps(state, indent=2)
            
            # Создаем или обновляем файл в репозитории
            try:
                file = self.repo.get_contents(filename)
                self.repo.update_file(
                    filename,
                    f"Update AI progress for {self.player_id}",
                    content,
                    file.sha
                )
            except:
                self.repo.create_file(
                    filename,
                    f"Create AI progress for {self.player_id}",
                    content
                )
            return True
        except Exception as e:
            print(f"Error saving progress: {e}")
            return False

    def load_progress(self) -> Optional[Dict]:
        try:
            # Получаем все файлы прогресса для данного игрока
            contents = self.repo.get_contents("progress")
            player_files = [
                content for content in contents 
                if content.path.startswith(f"progress/{self.player_id}_")
            ]
            
            if not player_files:
                return None
                
            # Находим самый последний файл
            latest_file = max(
                player_files,
                key=lambda x: x.path.split('_')[1].split('.')[0]
            )
            
            # Загружаем содержимое
            content = base64.b64decode(latest_file.content).decode('utf-8')
            return json.loads(content)
        except Exception as e:
            print(f"Error loading progress: {e}")
            return None
