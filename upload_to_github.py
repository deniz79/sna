#!/usr/bin/env python3
"""
GitHub'a Bot Kodlarını Yükleme Scripti
"""

import os
import subprocess
from pathlib import Path

def create_github_repository():
    """GitHub repository oluştur"""
    print("🚀 GITHUB REPOSITORY OLUŞTURMA")
    print("=" * 50)
    
    # README.md oluştur
    readme_content = """# DenizYetik-HybridBot

Advanced hybrid chess bot with deep learning system, position analysis, and adaptive engine selection.

## 🎯 Features

- **Hybrid Engine System**: Combines Stockfish 17.1 with planned LCZero integration
- **Deep Learning**: SQLite-based mistake database for continuous improvement
- **Position Analysis**: Advanced classification system for optimal engine selection
- **Anti-Stockfish Book**: Specialized Polyglot opening book
- **Endgame Tablebase**: Syzygy 5-6 piece tablebase integration
- **Visual Display**: Unicode chess board with real-time analysis
- **50-Move Rule**: Properly implemented FIDE rules

## 📊 Performance

- **Rating Estimate**: 2600
- **Total Games**: 5
- **Win Rate**: 20% (1 win, 4 draws, 0 losses)
- **Engine**: Stockfish 17.1
- **Language**: Python 3

## 🛠️ Installation

```bash
# Clone repository
git clone https://github.com/denizyetik/chess-bot.git
cd chess-bot

# Install dependencies
pip install -r requirements.txt

# Install Stockfish
brew install stockfish  # macOS
# sudo apt install stockfish  # Ubuntu

# Run bot
python3 main.py --hybrid
```

## 🎮 Usage

### Basic Usage
```bash
python3 main.py
```

### Hybrid Engine Mode
```bash
python3 main.py --hybrid
```

### Detailed Single Match
```bash
python3 detailed_single_match.py
```

### Tournament System
```bash
python3 continuous_tournament_system.py
```

## 📁 Project Structure

```
chess-bot/
├── main.py                          # Main entry point
├── detailed_single_match.py         # Detailed match system
├── continuous_tournament_system.py  # Tournament system
├── bot_profile.py                   # Bot profile generator
├── config.py                        # Configuration
├── requirements.txt                 # Dependencies
├── data/                           # Databases and data
│   ├── tournament_database.db
│   ├── learning_database.db
│   └── continuous_tournament_database.db
└── README.md                       # This file
```

## 🤖 Bot Features

### Engine Integration
- Stockfish 17.1 with optimized parameters
- Planned LCZero integration for strategic positions
- Dynamic engine selection based on position analysis

### Learning System
- SQLite database for storing position analyses
- Mistake tracking and avoidance
- Continuous improvement through self-play

### Opening Book
- Anti-Stockfish Polyglot book
- Surprise opening variations
- Position-specific move selection

### Time Management
- Dynamic time allocation based on position complexity
- Adaptive depth and analysis time
- Efficient resource utilization

## 📈 Statistics

- **Total Games Played**: 5
- **Wins**: 1 (20%)
- **Draws**: 4 (80%)
- **Losses**: 0 (0%)
- **Average Game Length**: 247 moves
- **Longest Game**: 361 moves

## 🔧 Configuration

Edit `config.py` to customize:
- Engine paths
- Analysis parameters
- Database settings
- Tournament configurations

## 📝 License

MIT License - see LICENSE file for details

## 👤 Author

**Deniz Yetik**
- GitHub: [@denizyetik](https://github.com/denizyetik)
- Bot Rating: 2600
- Specialization: Hybrid chess AI systems

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📞 Support

For questions and support:
- Create an issue on GitHub
- Contact: denizyetik@example.com

---

**DenizYetik-HybridBot** - Pushing the boundaries of chess AI! ♟️🤖
"""
    
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)
    
    print("✅ README.md oluşturuldu")
    
    # .gitignore oluştur
    gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Chess Data
*.pgn
*.bin
*.rtbw
*.rtbz

# Logs
*.log

# Database backups
*.db.backup
"""
    
    with open(".gitignore", "w") as f:
        f.write(gitignore_content)
    
    print("✅ .gitignore oluşturuldu")
    
    # LICENSE oluştur
    license_content = """MIT License

Copyright (c) 2025 Deniz Yetik

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
    
    with open("LICENSE", "w") as f:
        f.write(license_content)
    
    print("✅ LICENSE oluşturuldu")

def git_commands():
    """Git komutlarını çalıştır"""
    print("\n📤 GITHUB'A YÜKLEME")
    print("=" * 50)
    
    commands = [
        "git init",
        "git add .",
        "git commit -m 'Initial commit: DenizYetik-HybridBot chess AI'",
        "git branch -M main",
        "git remote add origin https://github.com/denizyetik/chess-bot.git",
        "git push -u origin main"
    ]
    
    for cmd in commands:
        print(f"🔄 Çalıştırılıyor: {cmd}")
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Başarılı: {cmd}")
            else:
                print(f"⚠️  Uyarı: {cmd}")
                print(f"   Hata: {result.stderr}")
        except Exception as e:
            print(f"❌ Hata: {cmd}")
            print(f"   Detay: {e}")

def create_github_instructions():
    """GitHub talimatları oluştur"""
    print("\n📋 GITHUB TALİMATLARI")
    print("=" * 50)
    
    instructions = """
🎯 GITHUB'A MANUEL YÜKLEME TALİMATLARI:

1️⃣ GitHub'da Repository Oluşturma:
   - https://github.com adresine gidin
   - "New repository" tıklayın
   - Repository name: chess-bot
   - Description: DenizYetik-HybridBot - Advanced chess AI
   - Public seçin
   - "Create repository" tıklayın

2️⃣ Dosyaları Yükleme:
   - "uploading an existing file" tıklayın
   - Tüm dosyaları sürükleyip bırakın:
     * main.py
     * detailed_single_match.py
     * continuous_tournament_system.py
     * bot_profile.py
     * config.py
     * requirements.txt
     * README.md
     * LICENSE
     * .gitignore

3️⃣ Commit Mesajı:
   - "Initial commit: DenizYetik-HybridBot chess AI"

4️⃣ Repository URL'i:
   - https://github.com/denizyetik/chess-bot

5️⃣ Bot Profilini Güncelleme:
   - bot_profile.json dosyasındaki github URL'ini güncelleyin
   - Repository linkini ekleyin

6️⃣ README.md'yi Özelleştirme:
   - Bot açıklamasını güncelleyin
   - Performans verilerini ekleyin
   - Kullanım talimatlarını detaylandırın

7️⃣ GitHub Pages (Opsiyonel):
   - Repository Settings → Pages
   - Source: Deploy from a branch
   - Branch: main
   - Folder: / (root)
   - Save

8️⃣ Bot Profilini Paylaşma:
   - README.md'yi sosyal medyada paylaşın
   - Chess forumlarında duyurun
   - GitHub'da star verin

🎉 Botunuz artık GitHub'da görünür olacak!
"""
    
    print(instructions)

def main():
    """Ana fonksiyon"""
    print("🚀 DENİZYETİK-HYBRİDBOT GITHUB YÜKLEME")
    print("=" * 60)
    
    # Dosyaları oluştur
    create_github_repository()
    
    # Git komutlarını çalıştır
    git_commands()
    
    # Talimatları göster
    create_github_instructions()
    
    print("\n🎉 İŞLEM TAMAMLANDI!")
    print("📁 Repository: https://github.com/denizyetik/chess-bot")
    print("📖 README: https://github.com/denizyetik/chess-bot/blob/main/README.md")

if __name__ == "__main__":
    main()
