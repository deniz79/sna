#!/usr/bin/env python3
"""
Detaylı Maç Analiz Sistemi
Tüm maçların istatistiklerini ve hamlelerini gösterir
"""

import sqlite3
import json
import chess
import chess.pgn
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

class DetailedMatchAnalyzer:
    """Detaylı maç analiz sistemi"""
    
    def __init__(self):
        self.tournament_db = Path("data/tournament_database.db")
        self.learning_db = Path("data/learning_database.db")
    
    def get_all_matches_with_moves(self) -> Dict:
        """Tüm maçları hamleleriyle birlikte al"""
        matches = []
        
        # Turnuva veritabanından
        if self.tournament_db.exists():
            conn = sqlite3.connect(self.tournament_db)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT tournament_id, game_id, result, moves, timestamp
                FROM game_results 
                ORDER BY timestamp DESC
            ''')
            
            for row in cursor.fetchall():
                tournament_id, game_id, result, moves, timestamp = row
                moves_data = json.loads(moves) if moves else []
                
                matches.append({
                    'source': 'Tournament',
                    'tournament_id': tournament_id,
                    'game_id': game_id,
                    'result': result,
                    'moves': moves_data,
                    'move_count': len(moves_data),
                    'timestamp': timestamp,
                    'winner': self._get_winner(result)
                })
            
            conn.close()
        
        # Öğrenme veritabanından
        if self.learning_db.exists():
            conn = sqlite3.connect(self.learning_db)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT game_id, result, moves, timestamp
                FROM game_results 
                ORDER BY timestamp DESC
            ''')
            
            for row in cursor.fetchall():
                game_id, result, moves, timestamp = row
                moves_data = json.loads(moves) if moves else []
                
                matches.append({
                    'source': 'Learning',
                    'tournament_id': 'Learning System',
                    'game_id': game_id,
                    'result': result,
                    'moves': moves_data,
                    'move_count': len(moves_data),
                    'timestamp': timestamp,
                    'winner': self._get_winner(result)
                })
            
            conn.close()
        
        return matches
    
    def _get_winner(self, result: str) -> str:
        """Kazananı belirle"""
        if result == "1-0":
            return "Beyaz (Bot)"
        elif result == "0-1":
            return "Siyah (Stockfish)"
        else:
            return "Beraberlik"
    
    def display_all_matches(self):
        """Tüm maçları göster"""
        matches = self.get_all_matches_with_moves()
        
        print("🏆 TÜM MAÇLARIN DETAYLI ANALİZİ")
        print("=" * 80)
        
        if not matches:
            print("❌ Henüz hiç maç oynanmamış!")
            return
        
        # Genel istatistikler
        total_matches = len(matches)
        total_wins = sum(1 for match in matches if match['result'] == "1-0")
        total_draws = sum(1 for match in matches if match['result'] == "1/2-1/2")
        total_losses = sum(1 for match in matches if match['result'] == "0-1")
        total_moves = sum(match['move_count'] for match in matches)
        avg_moves = total_moves / total_matches if total_matches > 0 else 0
        
        print(f"📊 GENEL İSTATİSTİKLER:")
        print(f"   Toplam maç: {total_matches}")
        print(f"   Kazanma: {total_wins}")
        print(f"   Beraberlik: {total_draws}")
        print(f"   Kaybetme: {total_losses}")
        print(f"   Skor: {total_wins}-{total_draws}-{total_losses}")
        print(f"   Kazanma oranı: {total_wins/total_matches:.1%}" if total_matches > 0 else "   Kazanma oranı: 0%")
        print(f"   Toplam hamle: {total_moves}")
        print(f"   Ortalama hamle: {avg_moves:.1f}")
        
        # Her maçın detayı
        print(f"\n🎮 TÜM MAÇLARIN DETAYI:")
        print("=" * 80)
        
        for i, match in enumerate(matches, 1):
            timestamp = datetime.fromisoformat(match['timestamp']) if match['timestamp'] else "Bilinmiyor"
            time_str = timestamp.strftime("%d/%m/%Y %H:%M") if isinstance(timestamp, datetime) else "Bilinmiyor"
            
            result_emoji = "🎉" if match['result'] == "1-0" else "😔" if match['result'] == "0-1" else "🤝"
            
            print(f"\n{i:2d}. {result_emoji} MAÇ {i}")
            print(f"    Kaynak: {match['source']}")
            print(f"    Turnuva: {match['tournament_id']}")
            print(f"    Oyun ID: {match['game_id']}")
            print(f"    Sonuç: {match['result']}")
            print(f"    Kazanan: {match['winner']}")
            print(f"    Hamle sayısı: {match['move_count']}")
            print(f"    Tarih: {time_str}")
            
            # Hamleleri göster
            if match['moves']:
                print(f"    📝 HAMLELER:")
                moves_text = ""
                for j, move_data in enumerate(match['moves'], 1):
                    move_num = (j + 1) // 2
                    if j % 2 == 1:  # Beyaz hamlesi
                        moves_text += f"{move_num:2d}. {move_data['san']:6}"
                    else:  # Siyah hamlesi
                        moves_text += f"{move_data['san']:6} "
                        if j % 10 == 0:  # Her 5 hamlede yeni satır
                            print(f"       {moves_text}")
                            moves_text = ""
                
                # Kalan hamleleri yazdır
                if moves_text.strip():
                    print(f"       {moves_text}")
            
            print("-" * 60)
    
    def display_match_by_id(self, game_id: str):
        """Belirli bir maçı ID ile göster"""
        matches = self.get_all_matches_with_moves()
        
        target_match = None
        for match in matches:
            if match['game_id'] == game_id:
                target_match = match
                break
        
        if not target_match:
            print(f"❌ {game_id} ID'li maç bulunamadı!")
            return
        
        print(f"🎯 MAÇ DETAYI: {game_id}")
        print("=" * 60)
        
        timestamp = datetime.fromisoformat(target_match['timestamp']) if target_match['timestamp'] else "Bilinmiyor"
        time_str = timestamp.strftime("%d/%m/%Y %H:%M:%S") if isinstance(timestamp, datetime) else "Bilinmiyor"
        
        print(f"Kaynak: {target_match['source']}")
        print(f"Turnuva: {target_match['tournament_id']}")
        print(f"Sonuç: {target_match['result']}")
        print(f"Kazanan: {target_match['winner']}")
        print(f"Hamle sayısı: {target_match['move_count']}")
        print(f"Tarih: {time_str}")
        
        # Hamleleri detaylı göster
        if target_match['moves']:
            print(f"\n📝 DETAYLI HAMLELER:")
            print("-" * 40)
            
            for i, move_data in enumerate(target_match['moves'], 1):
                move_num = (i + 1) // 2
                color = "Beyaz" if i % 2 == 1 else "Siyah"
                player = "Bot" if i % 2 == 1 else "Stockfish"
                
                print(f"{i:3d}. {move_num:2d}. {color:6} ({player:8}): {move_data['san']:6} ({move_data['uci']})")
                
                # Ek bilgiler varsa göster
                if 'analysis_time' in move_data:
                    print(f"     Analiz süresi: {move_data['analysis_time']:.2f}s")
                if 'think_time' in move_data:
                    print(f"     Düşünme süresi: {move_data['think_time']:.2f}s")
                if 'evaluation' in move_data and move_data['evaluation'] is not None:
                    print(f"     Değerlendirme: {move_data['evaluation']:.2f}")
    
    def get_match_statistics(self) -> Dict:
        """Maç istatistiklerini al"""
        matches = self.get_all_matches_with_moves()
        
        if not matches:
            return {"message": "Henüz hiç maç oynanmamış"}
        
        # Temel istatistikler
        total_matches = len(matches)
        total_wins = sum(1 for match in matches if match['result'] == "1-0")
        total_draws = sum(1 for match in matches if match['result'] == "1/2-1/2")
        total_losses = sum(1 for match in matches if match['result'] == "0-1")
        
        # Hamle istatistikleri
        move_counts = [match['move_count'] for match in matches]
        shortest_game = min(move_counts) if move_counts else 0
        longest_game = max(move_counts) if move_counts else 0
        avg_moves = sum(move_counts) / len(move_counts) if move_counts else 0
        
        # Kaynak bazlı istatistikler
        tournament_matches = [m for m in matches if m['source'] == 'Tournament']
        learning_matches = [m for m in matches if m['source'] == 'Learning']
        
        tournament_wins = sum(1 for match in tournament_matches if match['result'] == "1-0")
        learning_wins = sum(1 for match in learning_matches if match['result'] == "1-0")
        
        return {
            'total_matches': total_matches,
            'total_wins': total_wins,
            'total_draws': total_draws,
            'total_losses': total_losses,
            'win_rate': total_wins / total_matches if total_matches > 0 else 0,
            'shortest_game': shortest_game,
            'longest_game': longest_game,
            'average_moves': avg_moves,
            'tournament_matches': len(tournament_matches),
            'tournament_wins': tournament_wins,
            'tournament_win_rate': tournament_wins / len(tournament_matches) if tournament_matches else 0,
            'learning_matches': len(learning_matches),
            'learning_wins': learning_wins,
            'learning_win_rate': learning_wins / len(learning_matches) if learning_matches else 0
        }
    
    def display_advanced_statistics(self):
        """Gelişmiş istatistikleri göster"""
        stats = self.get_match_statistics()
        
        if "message" in stats:
            print(f"❌ {stats['message']}")
            return
        
        print("📈 GELİŞMİŞ İSTATİSTİKLER")
        print("=" * 60)
        
        print(f"🎮 OYUN İSTATİSTİKLERİ:")
        print(f"   En kısa oyun: {stats['shortest_game']} hamle")
        print(f"   En uzun oyun: {stats['longest_game']} hamle")
        print(f"   Ortalama hamle: {stats['average_moves']:.1f}")
        
        print(f"\n🏆 KAYNAK BAZLI İSTATİSTİKLER:")
        print(f"   Turnuva maçları: {stats['tournament_matches']}")
        print(f"   Turnuva kazanma: {stats['tournament_wins']}")
        print(f"   Turnuva kazanma oranı: {stats['tournament_win_rate']:.1%}")
        print(f"   Öğrenme maçları: {stats['learning_matches']}")
        print(f"   Öğrenme kazanma: {stats['learning_wins']}")
        print(f"   Öğrenme kazanma oranı: {stats['learning_win_rate']:.1%}")
        
        # Performans karşılaştırması
        if stats['tournament_matches'] > 0 and stats['learning_matches'] > 0:
            diff = stats['tournament_win_rate'] - stats['learning_win_rate']
            print(f"\n📊 PERFORMANS KARŞILAŞTIRMASI:")
            print(f"   Turnuva vs Öğrenme farkı: {diff:+.1%}")
            if diff > 0:
                print(f"   Turnuva sisteminde daha iyi performans!")
            elif diff < 0:
                print(f"   Öğrenme sisteminde daha iyi performans!")
            else:
                print(f"   Her iki sistemde de aynı performans!")
    
    def search_matches_by_result(self, result: str) -> List[Dict]:
        """Belirli sonuçtaki maçları ara"""
        matches = self.get_all_matches_with_moves()
        return [match for match in matches if match['result'] == result]
    
    def get_longest_matches(self, count: int = 5) -> List[Dict]:
        """En uzun maçları al"""
        matches = self.get_all_matches_with_moves()
        return sorted(matches, key=lambda x: x['move_count'], reverse=True)[:count]
    
    def get_shortest_matches(self, count: int = 5) -> List[Dict]:
        """En kısa maçları al"""
        matches = self.get_all_matches_with_moves()
        return sorted(matches, key=lambda x: x['move_count'])[:count]

def main():
    """Ana fonksiyon"""
    analyzer = DetailedMatchAnalyzer()
    
    try:
        # Tüm maçları göster
        analyzer.display_all_matches()
        
        # Gelişmiş istatistikler
        print(f"\n" + "="*80)
        analyzer.display_advanced_statistics()
        
        # En uzun maçlar
        print(f"\n🏆 EN UZUN 3 MAÇ:")
        longest_matches = analyzer.get_longest_matches(3)
        for i, match in enumerate(longest_matches, 1):
            timestamp = datetime.fromisoformat(match['timestamp']) if match['timestamp'] else "Bilinmiyor"
            time_str = timestamp.strftime("%d/%m %H:%M") if isinstance(timestamp, datetime) else "Bilinmiyor"
            
            print(f"   {i}. {match['game_id']}: {match['move_count']} hamle - {match['result']} - {time_str}")
        
        # En kısa maçlar
        print(f"\n⚡ EN KISA 3 MAÇ:")
        shortest_matches = analyzer.get_shortest_matches(3)
        for i, match in enumerate(shortest_matches, 1):
            timestamp = datetime.fromisoformat(match['timestamp']) if match['timestamp'] else "Bilinmiyor"
            time_str = timestamp.strftime("%d/%m %H:%M") if isinstance(timestamp, datetime) else "Bilinmiyor"
            
            print(f"   {i}. {match['game_id']}: {match['move_count']} hamle - {match['result']} - {time_str}")
        
        # Kazanan maçlar
        print(f"\n🎉 KAZANAN MAÇLAR:")
        winning_matches = analyzer.search_matches_by_result("1-0")
        for i, match in enumerate(winning_matches[:5], 1):
            timestamp = datetime.fromisoformat(match['timestamp']) if match['timestamp'] else "Bilinmiyor"
            time_str = timestamp.strftime("%d/%m %H:%M") if isinstance(timestamp, datetime) else "Bilinmiyor"
            
            print(f"   {i}. {match['game_id']}: {match['move_count']} hamle - {time_str}")
        
        # Örnek maç detayı
        matches = analyzer.get_all_matches_with_moves()
        if matches:
            print(f"\n🔍 ÖRNEK MAÇ DETAYI:")
            sample_match = matches[0]
            analyzer.display_match_by_id(sample_match['game_id'])
            
    except Exception as e:
        print(f"❌ Hata: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
