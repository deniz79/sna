#!/usr/bin/env python3
"""
Sürekli Turnuva Sonuçlarını Göster
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime

def show_continuous_results():
    """Sürekli turnuva sonuçlarını göster"""
    db_path = Path("data/continuous_tournament_database.db")
    
    if not db_path.exists():
        print("❌ Sürekli turnuva veritabanı bulunamadı!")
        print("💡 Henüz sürekli turnuva oynanmamış olabilir.")
        return
    
    print("🏆 SÜREKLİ TURNUVA SONUÇLARI")
    print("=" * 60)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Turnuva sonuçları
    cursor.execute('''
        SELECT tournament_id, games_played, wins, draws, losses, win_rate, 
               total_moves, average_game_length, timestamp
        FROM tournament_results 
        ORDER BY timestamp DESC
    ''')
    
    tournaments = cursor.fetchall()
    
    if not tournaments:
        print("❌ Henüz turnuva sonucu yok!")
        return
    
    print(f"📊 TOPLAM TURNUVA: {len(tournaments)}")
    print()
    
    # Genel istatistikler
    total_games = sum(t[1] for t in tournaments)
    total_wins = sum(t[2] for t in tournaments)
    total_draws = sum(t[3] for t in tournaments)
    total_losses = sum(t[4] for t in tournaments)
    overall_win_rate = total_wins / total_games if total_games > 0 else 0
    
    print(f"📈 GENEL İSTATİSTİKLER:")
    print(f"   Toplam oyun: {total_games}")
    print(f"   Toplam kazanma: {total_wins}")
    print(f"   Toplam beraberlik: {total_draws}")
    print(f"   Toplam kaybetme: {total_losses}")
    print(f"   Genel kazanma oranı: {overall_win_rate:.1%}")
    print()
    
    # Turnuva detayları
    print(f"🏆 TURNUVA DETAYLARI:")
    for i, tournament in enumerate(tournaments, 1):
        tournament_id, games_played, wins, draws, losses, win_rate, total_moves, avg_length, timestamp = tournament
        
        time_str = datetime.fromisoformat(timestamp).strftime("%d/%m %H:%M") if timestamp else "Bilinmiyor"
        
        print(f"   {i:2d}. {tournament_id}")
        print(f"       Skor: {wins}K {draws}B {losses}Y")
        print(f"       Kazanma oranı: {win_rate:.1%}")
        print(f"       Ortalama hamle: {avg_length:.1f}")
        print(f"       Tarih: {time_str}")
        print()
    
    # Oyun sonuçları
    cursor.execute('''
        SELECT tournament_id, game_id, result, moves, timestamp
        FROM game_results 
        ORDER BY timestamp DESC
        LIMIT 20
    ''')
    
    games = cursor.fetchall()
    
    if games:
        print(f"🎮 SON 20 OYUN:")
        for i, game in enumerate(games, 1):
            tournament_id, game_id, result, moves, timestamp = game
            
            moves_data = json.loads(moves) if moves else []
            move_count = len(moves_data)
            
            time_str = datetime.fromisoformat(timestamp).strftime("%d/%m %H:%M") if timestamp else "Bilinmiyor"
            
            result_emoji = "🎉" if result == "1-0" else "😔" if result == "0-1" else "🤝"
            
            print(f"   {i:2d}. {result_emoji} {game_id}")
            print(f"       Sonuç: {result} ({move_count} hamle)")
            print(f"       Turnuva: {tournament_id}")
            print(f"       Tarih: {time_str}")
            print()
    
    conn.close()

def show_all_databases():
    """Tüm veritabanlarından verileri göster"""
    print("🗄️ TÜM VERİTABANLARI")
    print("=" * 60)
    
    databases = [
        ("Tournament Database", "data/tournament_database.db"),
        ("Learning Database", "data/learning_database.db"),
        ("Continuous Tournament Database", "data/continuous_tournament_database.db")
    ]
    
    total_games = 0
    total_wins = 0
    total_draws = 0
    total_losses = 0
    
    for db_name, db_path in databases:
        path = Path(db_path)
        if not path.exists():
            print(f"❌ {db_name}: Bulunamadı")
            continue
        
        print(f"\n📊 {db_name}:")
        print("-" * 40)
        
        try:
            conn = sqlite3.connect(path)
            cursor = conn.cursor()
            
            # Oyun sayısı
            cursor.execute('SELECT COUNT(*) FROM game_results')
            game_count = cursor.fetchone()[0]
            
            # Kazanma sayısı
            cursor.execute('SELECT COUNT(*) FROM game_results WHERE result = "1-0"')
            win_count = cursor.fetchone()[0]
            
            # Beraberlik sayısı
            cursor.execute('SELECT COUNT(*) FROM game_results WHERE result = "1/2-1/2"')
            draw_count = cursor.fetchone()[0]
            
            # Kaybetme sayısı
            cursor.execute('SELECT COUNT(*) FROM game_results WHERE result = "0-1"')
            loss_count = cursor.fetchone()[0]
            
            win_rate = win_count / game_count if game_count > 0 else 0
            
            print(f"   Oyun sayısı: {game_count}")
            print(f"   Kazanma: {win_count}")
            print(f"   Beraberlik: {draw_count}")
            print(f"   Kaybetme: {loss_count}")
            print(f"   Kazanma oranı: {win_rate:.1%}")
            
            total_games += game_count
            total_wins += win_count
            total_draws += draw_count
            total_losses += loss_count
            
            conn.close()
            
        except Exception as e:
            print(f"   ❌ Hata: {e}")
    
    # Genel toplam
    if total_games > 0:
        overall_win_rate = total_wins / total_games
        print(f"\n🏆 GENEL TOPLAM:")
        print(f"   Toplam oyun: {total_games}")
        print(f"   Toplam kazanma: {total_wins}")
        print(f"   Toplam beraberlik: {total_draws}")
        print(f"   Toplam kaybetme: {total_losses}")
        print(f"   Genel kazanma oranı: {overall_win_rate:.1%}")

def main():
    """Ana fonksiyon"""
    print("📊 VERİ ANALİZİ")
    print("=" * 60)
    
    # Sürekli turnuva sonuçları
    show_continuous_results()
    
    print("\n" + "=" * 60)
    
    # Tüm veritabanları
    show_all_databases()

if __name__ == "__main__":
    main()
