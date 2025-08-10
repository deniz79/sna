#!/usr/bin/env python3
"""
Maç Sonuçları Analiz Sistemi
Geçmiş maçları analiz eder ve skorları gösterir
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

class MatchResultsAnalyzer:
    """Maç sonuçları analiz sistemi"""
    
    def __init__(self):
        self.tournament_db = Path("data/tournament_database.db")
        self.learning_db = Path("data/learning_database.db")
    
    def get_all_match_results(self) -> Dict:
        """Tüm maç sonuçlarını al"""
        results = {
            'tournaments': [],
            'individual_games': [],
            'total_stats': {}
        }
        
        # Turnuva veritabanından
        if self.tournament_db.exists():
            conn = sqlite3.connect(self.tournament_db)
            cursor = conn.cursor()
            
            # Turnuva sonuçları
            cursor.execute('''
                SELECT tournament_id, games_played, wins, draws, losses, win_rate, 
                       total_moves, average_game_length, timestamp
                FROM tournament_results 
                ORDER BY timestamp DESC
            ''')
            
            for row in cursor.fetchall():
                tournament_id, games_played, wins, draws, losses, win_rate, total_moves, avg_length, timestamp = row
                results['tournaments'].append({
                    'tournament_id': tournament_id,
                    'games_played': games_played,
                    'wins': wins,
                    'draws': draws,
                    'losses': losses,
                    'win_rate': win_rate,
                    'total_moves': total_moves,
                    'average_game_length': avg_length,
                    'timestamp': timestamp,
                    'score': f"{wins}-{draws}-{losses}"
                })
            
            # Bireysel oyun sonuçları
            cursor.execute('''
                SELECT tournament_id, game_id, result, moves, timestamp
                FROM game_results 
                ORDER BY timestamp DESC
            ''')
            
            for row in cursor.fetchall():
                tournament_id, game_id, result, moves, timestamp = row
                moves_data = json.loads(moves) if moves else []
                
                results['individual_games'].append({
                    'tournament_id': tournament_id,
                    'game_id': game_id,
                    'result': result,
                    'move_count': len(moves_data),
                    'timestamp': timestamp,
                    'winner': self._get_winner(result)
                })
            
            conn.close()
        
        # Öğrenme veritabanından
        if self.learning_db.exists():
            conn = sqlite3.connect(self.learning_db)
            cursor = conn.cursor()
            
            # Oyun sonuçları
            cursor.execute('''
                SELECT game_id, result, moves, timestamp
                FROM game_results 
                ORDER BY timestamp DESC
            ''')
            
            for row in cursor.fetchall():
                game_id, result, moves, timestamp = row
                moves_data = json.loads(moves) if moves else []
                
                results['individual_games'].append({
                    'tournament_id': 'Learning System',
                    'game_id': game_id,
                    'result': result,
                    'move_count': len(moves_data),
                    'timestamp': timestamp,
                    'winner': self._get_winner(result)
                })
            
            conn.close()
        
        # Genel istatistikler
        results['total_stats'] = self._calculate_total_stats(results)
        
        return results
    
    def _get_winner(self, result: str) -> str:
        """Kazananı belirle"""
        if result == "1-0":
            return "Beyaz (Bot)"
        elif result == "0-1":
            return "Siyah (Stockfish)"
        else:
            return "Beraberlik"
    
    def _calculate_total_stats(self, results: Dict) -> Dict:
        """Genel istatistikleri hesapla"""
        total_games = len(results['individual_games'])
        total_wins = sum(1 for game in results['individual_games'] if game['result'] == "1-0")
        total_draws = sum(1 for game in results['individual_games'] if game['result'] == "1/2-1/2")
        total_losses = sum(1 for game in results['individual_games'] if game['result'] == "0-1")
        
        win_rate = total_wins / total_games if total_games > 0 else 0.0
        
        return {
            'total_games': total_games,
            'total_wins': total_wins,
            'total_draws': total_draws,
            'total_losses': total_losses,
            'win_rate': win_rate,
            'score': f"{total_wins}-{total_draws}-{total_losses}"
        }
    
    def display_match_results(self):
        """Maç sonuçlarını göster"""
        print("🏆 MAÇ SONUÇLARI ANALİZİ")
        print("=" * 60)
        
        results = self.get_all_match_results()
        
        # Genel istatistikler
        stats = results['total_stats']
        print(f"📊 GENEL İSTATİSTİKLER:")
        print(f"   Toplam maç: {stats['total_games']}")
        print(f"   Kazanma: {stats['total_wins']}")
        print(f"   Beraberlik: {stats['total_draws']}")
        print(f"   Kaybetme: {stats['total_losses']}")
        print(f"   Skor: {stats['score']}")
        print(f"   Kazanma oranı: {stats['win_rate']:.1%}")
        
        # Son 10 maç
        print(f"\n🎮 SON 10 MAÇ:")
        recent_games = results['individual_games'][:10]
        
        for i, game in enumerate(recent_games, 1):
            timestamp = datetime.fromisoformat(game['timestamp']) if game['timestamp'] else "Bilinmiyor"
            time_str = timestamp.strftime("%d/%m %H:%M") if isinstance(timestamp, datetime) else "Bilinmiyor"
            
            result_emoji = "🎉" if game['result'] == "1-0" else "😔" if game['result'] == "0-1" else "🤝"
            
            print(f"   {i:2d}. {result_emoji} {game['tournament_id']} - {game['result']} ({game['move_count']} hamle) - {time_str}")
            print(f"       Kazanan: {game['winner']}")
        
        # Turnuva sonuçları
        if results['tournaments']:
            print(f"\n🏆 TURNUVA SONUÇLARI:")
            for tournament in results['tournaments'][:5]:  # Son 5 turnuva
                timestamp = datetime.fromisoformat(tournament['timestamp']) if tournament['timestamp'] else "Bilinmiyor"
                time_str = timestamp.strftime("%d/%m %H:%M") if isinstance(timestamp, datetime) else "Bilinmiyor"
                
                print(f"   {tournament['tournament_id']}: {tournament['score']} - {tournament['win_rate']:.1%} - {time_str}")
        
        # En iyi performans
        if results['tournaments']:
            best_tournament = max(results['tournaments'], key=lambda x: x['win_rate'])
            print(f"\n🏆 EN İYİ TURNUVA:")
            print(f"   {best_tournament['tournament_id']}: {best_tournament['score']} - {best_tournament['win_rate']:.1%}")
        
        # Son maçın detayı
        if results['individual_games']:
            last_game = results['individual_games'][0]
            print(f"\n🎯 SON MAÇ DETAYI:")
            print(f"   Turnuva: {last_game['tournament_id']}")
            print(f"   Oyun ID: {last_game['game_id']}")
            print(f"   Sonuç: {last_game['result']}")
            print(f"   Kazanan: {last_game['winner']}")
            print(f"   Hamle sayısı: {last_game['move_count']}")
            
            timestamp = datetime.fromisoformat(last_game['timestamp']) if last_game['timestamp'] else "Bilinmiyor"
            if isinstance(timestamp, datetime):
                print(f"   Tarih: {timestamp.strftime('%d/%m/%Y %H:%M:%S')}")
    
    def get_recent_match_details(self, match_count: int = 5) -> List[Dict]:
        """Son maçların detaylarını al"""
        results = self.get_all_match_results()
        return results['individual_games'][:match_count]
    
    def search_match_by_id(self, game_id: str) -> Dict:
        """Belirli bir maçı ID ile ara"""
        results = self.get_all_match_results()
        
        for game in results['individual_games']:
            if game['game_id'] == game_id:
                return game
        
        return None
    
    def get_performance_trend(self) -> Dict:
        """Performans trendini analiz et"""
        results = self.get_all_match_results()
        
        # Son 20 maçın performansı
        recent_games = results['individual_games'][:20]
        
        if len(recent_games) < 10:
            return {"message": "Yeterli veri yok"}
        
        # İlk 10 maç vs son 10 maç
        first_10 = recent_games[-10:]
        last_10 = recent_games[:10]
        
        first_10_wins = sum(1 for game in first_10 if game['result'] == "1-0")
        last_10_wins = sum(1 for game in last_10 if game['result'] == "1-0")
        
        first_10_rate = first_10_wins / 10
        last_10_rate = last_10_wins / 10
        
        improvement = last_10_rate - first_10_rate
        
        return {
            "first_10_games": {
                "wins": first_10_wins,
                "win_rate": first_10_rate,
                "score": f"{first_10_wins}-{10-first_10_wins}"
            },
            "last_10_games": {
                "wins": last_10_wins,
                "win_rate": last_10_rate,
                "score": f"{last_10_wins}-{10-last_10_wins}"
            },
            "improvement": improvement,
            "trend": "İyileşme" if improvement > 0 else "Kötüleşme" if improvement < 0 else "Stabil"
        }

def main():
    """Ana fonksiyon"""
    analyzer = MatchResultsAnalyzer()
    
    try:
        # Maç sonuçlarını göster
        analyzer.display_match_results()
        
        # Performans trendi
        print(f"\n📈 PERFORMANS TRENDİ:")
        trend = analyzer.get_performance_trend()
        
        if "message" not in trend:
            print(f"   İlk 10 maç: {trend['first_10_games']['score']} ({trend['first_10_games']['win_rate']:.1%})")
            print(f"   Son 10 maç: {trend['last_10_games']['score']} ({trend['last_10_games']['win_rate']:.1%})")
            print(f"   Değişim: {trend['improvement']:+.1%} ({trend['trend']})")
        else:
            print(f"   {trend['message']}")
        
        # Son maçların detayları
        print(f"\n🔍 SON MAÇLARIN DETAYLARI:")
        recent_matches = analyzer.get_recent_match_details(3)
        
        for i, match in enumerate(recent_matches, 1):
            print(f"\n   {i}. MAÇ:")
            print(f"      Turnuva: {match['tournament_id']}")
            print(f"      Sonuç: {match['result']}")
            print(f"      Kazanan: {match['winner']}")
            print(f"      Hamle: {match['move_count']}")
            
    except Exception as e:
        print(f"❌ Hata: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
