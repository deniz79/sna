"""
Santranç Bot Konfigürasyon Dosyası
"""

import os
from pathlib import Path

# Proje kök dizini
PROJECT_ROOT = Path(__file__).parent

# Veri dizinleri
DATA_DIR = PROJECT_ROOT / "data"
BOOKS_DIR = DATA_DIR / "books"
PGN_DIR = DATA_DIR / "pgn"
TABLEBASES_DIR = DATA_DIR / "tablebases"
LOGS_DIR = PROJECT_ROOT / "logs"

# Motor yolları
ENGINES = {
    "stockfish": {
        "path": "/opt/homebrew/bin/stockfish",
        "name": "Stockfish 17.1",
        "options": {
            "Threads": 4,
            "Hash": 1024,
            "Contempt": 0,
            "SyzygyPath": str(TABLEBASES_DIR),
            "SyzygyProbeLimit": 6
        }
    },
    "lc0": {
        "path": "/usr/local/bin/lc0",
        "name": "Leela Chess Zero",
        "options": {
            "Backend": "cuda",
            "Threads": 4,
            "MinibatchSize": 256
        }
    }
}

# Açılış kitabı ayarları
BOOK_CONFIG = {
    "default_book": "anti_stockfish.bin",
    "max_book_moves": 15,  # İlk kaç hamlede kitap kullanılacak
    "min_weight": 1,       # Minimum ağırlık
    "max_weight": 100      # Maksimum ağırlık
}

# Oyun ayarları
GAME_CONFIG = {
    "time_control": "5+3",  # 5 dakika + 3 saniye increment
    "max_moves": 200,       # Maksimum hamle sayısı
    "tablebase_probe_limit": 6,  # Kaç taşa kadar tablebase kullanılacak
    "engine_time_limit": 0.5,    # Motor için zaman limiti (saniye)
    "book_probability": 0.8      # Kitap kullanma olasılığı
}

# Test ayarları
TEST_CONFIG = {
    "games_per_test": 100,
    "concurrency": 4,      # Paralel oyun sayısı
    "output_pgn": "test_results.pgn",
    "engine1": "stockfish",
    "engine2": "our_bot"
}

# Logging ayarları
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": str(LOGS_DIR / "bot.log")
}

# PGN kaynakları (Stockfish'e karşı alınan galibiyetler için)
PGN_SOURCES = [
    "https://database.lichess.org/standard/lichess_db_standard_rated_2023-01.pgn.zst",
    "https://database.lichess.org/standard/lichess_db_standard_rated_2023-02.pgn.zst"
]

# Filtreleme kriterleri (Stockfish'e karşı başarılı varyantlar için)
FILTER_CRITERIA = {
    "min_rating": 2000,        # Minimum oyuncu rating'i
    "max_rating": 2800,        # Maksimum oyuncu rating'i
    "result_filter": "1-0",    # Sadece beyaz galibiyetleri
    "eco_codes": [             # İstenen ECO kodları (opsiyonel)
        "A00", "A01", "A02",   # Açık oyunlar
        "B00", "B01", "B02",   # Semi-Open oyunlar
        "C00", "C01", "C02",   # Kapalı oyunlar
        "D00", "D01", "D02",   # Queen's Pawn oyunları
        "E00", "E01", "E02"    # Indian oyunları
    ]
}

# Syzygy tablebase ayarları
SYZYGY_CONFIG = {
    "enabled": True,
    "path": str(TABLEBASES_DIR),
    "probe_limit": 6,
    "50_move_rule": True,
    "repetition_rule": True
}

# Gelişmiş motor ayarları
ADVANCED_ENGINE_CONFIG = {
    "multi_pv": 1,            # Principal variation sayısı
    "skill_level": 20,        # Skill level (0-20)
    "move_overhead": 10,      # Move overhead (ms)
    "slow_mover": 80,         # Slow mover yüzdesi
    "nodestime": 0,           # Node time (ms)
    "ponder": False,          # Ponder mode
    "uci_showcurrmoves": False,
    "uci_limitstrength": False,
    "uci_elo": 2850           # UCI Elo rating
}

# Otomatik kitap geliştirme ayarları
AUTO_BOOK_CONFIG = {
    "enabled": True,
    "min_games": 50,          # Minimum oyun sayısı
    "win_rate_threshold": 0.6, # Minimum kazanma oranı
    "update_frequency": 100,   # Her kaç oyunda bir güncelleme
    "max_book_size": 10000,    # Maksimum kitap boyutu
    "backup_books": True       # Kitap yedekleme
}

# Performans izleme
PERFORMANCE_CONFIG = {
    "track_metrics": True,
    "save_games": True,
    "analyze_positions": True,
    "generate_reports": True
}

def ensure_directories():
    """Gerekli dizinlerin varlığını kontrol et ve oluştur"""
    directories = [DATA_DIR, BOOKS_DIR, PGN_DIR, TABLEBASES_DIR, LOGS_DIR]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

def get_engine_path(engine_name):
    """Motor yolunu döndür"""
    if engine_name in ENGINES:
        return ENGINES[engine_name]["path"]
    return None

def get_book_path(book_name=None):
    """Kitap yolunu döndür"""
    if book_name is None:
        book_name = BOOK_CONFIG["default_book"]
    return BOOKS_DIR / book_name

# Dizinleri oluştur
ensure_directories()
