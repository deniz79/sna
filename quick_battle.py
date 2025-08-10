#!/usr/bin/env python3
"""
Stockfish 17.1 ile Hızlı Kapışma Scripti
"""

import chess
import chess.engine
import time
import logging
from pathlib import Path

# Logging ayarla
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def play_quick_game(our_engine_path: str, stockfish_path: str = "/opt/homebrew/bin/stockfish", 
                   time_control: str = "5+3", max_moves: int = 50):
    """Hızlı test maçı oyna"""
    
    print("🥊 Stockfish 17.1 ile Kapışma Başlıyor!")
    print("=" * 50)
    
    try:
        # Motorları başlat
        print("🚀 Motorlar başlatılıyor...")
        
        # Stockfish
        stockfish = chess.engine.SimpleEngine.popen_uci(stockfish_path)
        stockfish.configure({"Threads": 4, "Hash": 1024})
        
        # Bizim bot (hibrit sistem)
        from hybrid_engine import AdaptiveHybridEngine
        our_bot = AdaptiveHybridEngine()
        
        print("✅ Motorlar hazır!")
        
        # Oyun başlat
        board = chess.Board()
        move_count = 0
        
        print(f"\n🎮 Oyun başlıyor - Zaman kontrolü: {time_control}")
        print("Beyaz: Bizim Bot (Hibrit)")
        print("Siyah: Stockfish 17.1")
        print("-" * 50)
        
        # 50 hamle kuralı için sayaç
        moves_without_capture = 0
        last_capture_move = 0
        
        while not board.is_game_over() and move_count < max_moves:
            move_count += 1
            
            if board.turn == chess.WHITE:
                # Bizim bot
                print(f"\n{move_count}. Beyaz (Bizim Bot) düşünüyor...")
                start_time = time.time()
                
                move = our_bot.get_move(board, time_limit=2.0)
                
                end_time = time.time()
                think_time = end_time - start_time
                
                if move:
                    san_move = board.san(move)
                    print(f"   Hamle: {san_move} ({move.uci()}) - Süre: {think_time:.2f}s")
                    
                    # 50 hamle kuralı kontrolü
                    if board.is_capture(move):
                        moves_without_capture = 0
                    else:
                        moves_without_capture += 1
                    
                    board.push(move)
                    move_count += 1
                    
                    # 50 hamle kuralı kontrolü
                    if moves_without_capture >= 100:  # 50 hamle = 100 yarı hamle
                        print("   ⏰ 50 hamle kuralı! Beraberlik")
                        break
                else:
                    print("   ❌ Hamle bulunamadı!")
                    break
                    
            else:
                # Stockfish
                print(f"\n{move_count}. Siyah (Stockfish) düşünüyor...")
                start_time = time.time()
                
                result = stockfish.play(board, chess.engine.Limit(time=2.0))
                move = result.move
                
                end_time = time.time()
                think_time = end_time - start_time
                
                if move:
                    san_move = board.san(move)
                    print(f"   Hamle: {san_move} ({move.uci()}) - Süre: {think_time:.2f}s")
                    
                    # 50 hamle kuralı kontrolü
                    if board.is_capture(move):
                        moves_without_capture = 0
                    else:
                        moves_without_capture += 1
                    
                    board.push(move)
                    move_count += 1
                    
                    # 50 hamle kuralı kontrolü
                    if moves_without_capture >= 100:  # 50 hamle = 100 yarı hamle
                        print("   ⏰ 50 hamle kuralı! Beraberlik")
                        break
                else:
                    print("   ❌ Hamle bulunamadı!")
                    break
            
            # Pozisyonu göster
            print(f"   Pozisyon: {board.fen()}")
            
            # Şah tehdidi kontrolü
            if board.is_check():
                print("   ⚠️  ŞAH TEHDİDİ!")
        
        # Oyun sonucu
        print("\n" + "=" * 50)
        print("🏁 OYUN SONUCU")
        print("=" * 50)
        
        if board.is_game_over():
            if board.is_checkmate():
                winner = "Siyah" if board.turn == chess.WHITE else "Beyaz"
                print(f"🎯 ŞAH MAT! Kazanan: {winner}")
            elif board.is_stalemate():
                print("🤝 PAT! Beraberlik")
            elif board.is_insufficient_material():
                print("🤝 Yetersiz materyal! Beraberlik")
            elif board.is_fifty_moves():
                print("🤝 50 hamle kuralı! Beraberlik")
            elif board.is_repetition():
                print("🤝 Tekrar! Beraberlik")
        else:
            print(f"⏰ Maksimum hamle sayısına ulaşıldı ({max_moves})")
        
        print(f"📊 Toplam hamle: {move_count}")
        print(f"📝 Son pozisyon: {board.fen()}")
        
        # İstatistikler
        print("\n📈 İSTATİSTİKLER")
        print("-" * 30)
        
        # Hibrit bot istatistikleri
        stats = our_bot.get_learning_stats()
        decision_stats = stats.get('decision_history', {})
        
        print("Hibrit Bot Kararları:")
        for engine, count in decision_stats.get('engine_usage', {}).items():
            print(f"  {engine}: {count} kez kullanıldı")
        
        for pos_type, count in decision_stats.get('position_type_usage', {}).items():
            print(f"  {pos_type} pozisyonu: {count} kez")
        
        return board.result()
        
    except Exception as e:
        print(f"❌ Hata: {e}")
        return None
        
    finally:
        # Motorları kapat
        try:
            stockfish.quit()
            our_bot.close()
            print("\n✅ Motorlar kapatıldı")
        except:
            pass

def play_multiple_games(num_games: int = 5):
    """Birden fazla oyun oyna"""
    
    print(f"🏆 {num_games} Oyunluk Turnuva Başlıyor!")
    print("=" * 50)
    
    results = {
        'our_wins': 0,
        'stockfish_wins': 0,
        'draws': 0
    }
    
    for game_num in range(1, num_games + 1):
        print(f"\n🎮 OYUN {game_num}/{num_games}")
        print("-" * 30)
        
        result = play_quick_game("/opt/homebrew/bin/stockfish")
        
        if result == "1-0":
            results['our_wins'] += 1
            print("🎉 BİZ KAZANDIK!")
        elif result == "0-1":
            results['stockfish_wins'] += 1
            print("😔 Stockfish kazandı")
        else:
            results['draws'] += 1
            print("🤝 Beraberlik")
        
        # Kısa bekleme
        time.sleep(2)
    
    # Turnuva sonucu
    print("\n" + "=" * 50)
    print("🏆 TURNUVA SONUCU")
    print("=" * 50)
    print(f"Bizim Kazanma: {results['our_wins']}")
    print(f"Stockfish Kazanma: {results['stockfish_wins']}")
    print(f"Beraberlik: {results['draws']}")
    
    total_games = sum(results.values())
    if total_games > 0:
        our_win_rate = results['our_wins'] / total_games * 100
        print(f"\n📊 Bizim Kazanma Oranı: {our_win_rate:.1f}%")
        
        if our_win_rate > 50:
            print("🎉 TEBRİKLER! Stockfish'i yendiniz!")
        elif our_win_rate > 30:
            print("👍 İyi performans! Stockfish'e yaklaştınız!")
        else:
            print("💪 Daha fazla çalışma gerekli!")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Stockfish ile kapışma")
    parser.add_argument("--games", type=int, default=1, help="Oyun sayısı")
    parser.add_argument("--time", default="5+3", help="Zaman kontrolü")
    
    args = parser.parse_args()
    
    if args.games == 1:
        play_quick_game("/opt/homebrew/bin/stockfish")
    else:
        play_multiple_games(args.games)
