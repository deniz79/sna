# DenizYetik-HybridBot

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
