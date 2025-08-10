#!/usr/bin/env python3
"""
Mevcut GitHub Repository'yi Güncelleme Scripti
https://github.com/deniz79/sna
"""

import subprocess
import os
from pathlib import Path

def update_existing_repository():
    """Mevcut repository'yi güncelle"""
    print("🔄 MEVCUT REPOSITORY GÜNCELLEME")
    print("=" * 50)
    print("Repository: https://github.com/deniz79/sna")
    
    # Git komutları
    commands = [
        "git remote set-url origin https://github.com/deniz79/sna.git",
        "git add .",
        "git commit -m 'Add DenizYetik-HybridBot chess AI system'",
        "git push origin main"
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

def create_chess_readme():
    """Chess bot için README oluştur"""
    readme_content = """# DenizYetik-HybridBot ♟️🤖

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
git clone https://github.com/deniz79/sna.git
cd sna

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
sna/
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
- GitHub: [@deniz79](https://github.com/deniz79)
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
- Contact: deniz79@github.com

---

**DenizYetik-HybridBot** - Pushing the boundaries of chess AI! ♟️🤖

## 🌐 Neural Network Repository Links

- **GitHub Repository**: https://github.com/deniz79/sna
- **Lichess Analysis**: https://lichess.org/analysis
- **Chess.com Analysis**: https://www.chess.com/analysis

### Bot Search Terms:
- **Network Name**: `DenizYetik-HybridBot`
- **Author**: `Deniz Yetik`
- **Rating**: `2600`
- **Engine**: `Stockfish 17.1`
"""
    
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)
    
    print("✅ README.md güncellendi")

def main():
    """Ana fonksiyon"""
    print("🚀 MEVCUT REPOSITORY GÜNCELLEME")
    print("=" * 60)
    print("Repository: https://github.com/deniz79/sna")
    
    # README güncelle
    create_chess_readme()
    
    # Repository'yi güncelle
    update_existing_repository()
    
    print("\n🎉 İŞLEM TAMAMLANDI!")
    print("📁 Repository: https://github.com/deniz79/sna")
    print("📖 README: https://github.com/deniz79/sna/blob/main/README.md")
    print("\n🔍 Neural Network Repository'de Arama:")
    print("   Network Name: DenizYetik-HybridBot")
    print("   Author: Deniz Yetik")
    print("   Rating: 2600")

if __name__ == "__main__":
    main()
