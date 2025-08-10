#!/usr/bin/env python3
"""
Bot Profil Bilgileri
Neural Network Repository için bot bilgilerini hazırlar
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime

class BotProfile:
    """Bot profil bilgileri"""
    
    def __init__(self):
        self.bot_name = "DenizYetik-HybridBot"
        self.author = "Deniz Yetik"
        self.version = "1.0"
        self.description = "Hybrid chess bot with deep learning system, position analysis, and adaptive engine selection"
        
        # Veritabanları
        self.databases = [
            "data/tournament_database.db",
            "data/learning_database.db", 
            "data/continuous_tournament_database.db",
            "data/detailed_single_match.db"
        ]
    
    def get_bot_statistics(self):
        """Bot istatistiklerini al"""
        total_games = 0
        total_wins = 0
        total_draws = 0
        total_losses = 0
        
        for db_path in self.databases:
            path = Path(db_path)
            if path.exists():
                try:
                    conn = sqlite3.connect(path)
                    cursor = conn.cursor()
                    
                    # Oyun sonuçlarını al
                    cursor.execute("SELECT result FROM game_results")
                    results = cursor.fetchall()
                    
                    for result in results:
                        total_games += 1
                        if result[0] == "1-0":
                            total_wins += 1
                        elif result[0] == "0-1":
                            total_losses += 1
                        else:
                            total_draws += 1
                    
                    conn.close()
                except Exception as e:
                    print(f"Veritabanı hatası {db_path}: {e}")
        
        if total_games > 0:
            win_rate = (total_wins / total_games) * 100
            draw_rate = (total_draws / total_games) * 100
            loss_rate = (total_losses / total_games) * 100
        else:
            win_rate = draw_rate = loss_rate = 0
        
        return {
            "total_games": total_games,
            "wins": total_wins,
            "draws": total_draws,
            "losses": total_losses,
            "win_rate": win_rate,
            "draw_rate": draw_rate,
            "loss_rate": loss_rate
        }
    
    def get_bot_features(self):
        """Bot özelliklerini al"""
        return {
            "engines": ["Stockfish 17.1", "LCZero (planned)"],
            "opening_book": "Anti-Stockfish Polyglot Book",
            "endgame_tablebase": "Syzygy 5-6 piece",
            "position_analysis": "Advanced classification system",
            "learning_system": "SQLite-based mistake database",
            "time_management": "Dynamic allocation based on position",
            "50_move_rule": "Implemented correctly",
            "visual_display": "Unicode chess board"
        }
    
    def get_recent_games(self, limit=10):
        """Son oyunları al"""
        recent_games = []
        
        for db_path in self.databases:
            path = Path(db_path)
            if path.exists():
                try:
                    conn = sqlite3.connect(path)
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                        SELECT result, total_time, average_move_time, timestamp 
                        FROM game_results 
                        ORDER BY timestamp DESC 
                        LIMIT ?
                    """, (limit,))
                    
                    games = cursor.fetchall()
                    for game in games:
                        recent_games.append({
                            "result": game[0],
                            "total_time": game[1],
                            "avg_move_time": game[2],
                            "timestamp": game[3],
                            "database": path.name
                        })
                    
                    conn.close()
                except Exception as e:
                    print(f"Veritabanı hatası {db_path}: {e}")
        
        # Tarihe göre sırala
        recent_games.sort(key=lambda x: x["timestamp"], reverse=True)
        return recent_games[:limit]
    
    def create_bot_profile(self):
        """Bot profilini oluştur"""
        stats = self.get_bot_statistics()
        features = self.get_bot_features()
        recent_games = self.get_recent_games()
        
        profile = {
            "network_name": self.bot_name,
            "author": self.author,
            "version": self.version,
            "description": self.description,
            "created_date": datetime.now().isoformat(),
            "statistics": stats,
            "features": features,
            "recent_games": recent_games,
            "rating_estimate": self._estimate_rating(stats),
            "repository_info": {
                "github": "https://github.com/denizyetik/chess-bot",
                "license": "MIT",
                "language": "Python 3",
                "dependencies": ["python-chess", "stockfish", "sqlite3"]
            }
        }
        
        return profile
    
    def _estimate_rating(self, stats):
        """Rating tahmini"""
        if stats["total_games"] == 0:
            return 1500
        
        # Basit rating hesaplama
        base_rating = 2000  # Stockfish'e karşı oynadığımız için
        win_bonus = stats["win_rate"] * 2
        draw_bonus = stats["draw_rate"] * 0.5
        
        estimated_rating = base_rating + win_bonus + draw_bonus
        
        # Stockfish 17.1'in rating'i ~3500 civarı
        # Bizim botumuzun performansına göre ayarla
        if stats["win_rate"] > 50:
            estimated_rating = 2800 + (stats["win_rate"] - 50) * 10
        else:
            estimated_rating = 2500 + stats["win_rate"] * 5
        
        return int(estimated_rating)
    
    def save_profile(self, filename="bot_profile.json"):
        """Profili kaydet"""
        profile = self.create_bot_profile()
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(profile, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Bot profili kaydedildi: {filename}")
        return profile
    
    def display_profile(self):
        """Profili göster"""
        profile = self.create_bot_profile()
        
        print("🤖 BOT PROFİLİ")
        print("=" * 60)
        print(f"📛 İsim: {profile['network_name']}")
        print(f"👤 Yazar: {profile['author']}")
        print(f"📦 Versiyon: {profile['version']}")
        print(f"📊 Tahmini Rating: {profile['rating_estimate']}")
        print(f"📝 Açıklama: {profile['description']}")
        
        print(f"\n📈 İSTATİSTİKLER")
        print("-" * 40)
        stats = profile['statistics']
        print(f"🎮 Toplam Oyun: {stats['total_games']}")
        print(f"🏆 Galibiyet: {stats['wins']} ({stats['win_rate']:.1f}%)")
        print(f"🤝 Beraberlik: {stats['draws']} ({stats['draw_rate']:.1f}%)")
        print(f"❌ Mağlubiyet: {stats['losses']} ({stats['loss_rate']:.1f}%)")
        
        print(f"\n⚙️ ÖZELLİKLER")
        print("-" * 40)
        features = profile['features']
        for key, value in features.items():
            if isinstance(value, list):
                print(f"🔧 {key}: {', '.join(value)}")
            else:
                print(f"🔧 {key}: {value}")
        
        print(f"\n🎮 SON OYUNLAR")
        print("-" * 40)
        for i, game in enumerate(profile['recent_games'][:5], 1):
            result = game['result']
            if result == "1-0":
                result_str = "🏆 Bot Kazandı"
            elif result == "0-1":
                result_str = "❌ Stockfish Kazandı"
            else:
                result_str = "🤝 Beraberlik"
            
            print(f"{i}. {result_str} | Süre: {game['total_time']:.1f}s | DB: {game['database']}")
        
        return profile

def main():
    """Ana fonksiyon"""
    print("🤖 BOT PROFİLİ OLUŞTURUCU")
    print("=" * 60)
    
    bot = BotProfile()
    profile = bot.display_profile()
    
    # Profili kaydet
    bot.save_profile()
    
    print(f"\n💾 Neural Network Repository için hazır!")
    print(f"📁 Dosya: bot_profile.json")
    print(f"🌐 Bu dosyayı Neural Network Repository'ye yükleyebilirsiniz")

if __name__ == "__main__":
    main()
