"""
Ana Bot Wrapper - Tüm bileşenleri entegre eden ana sistem
"""

import chess
import chess.pgn
import logging
import time
import argparse
import sys
from pathlib import Path
from typing import Optional, Dict, Any

import config
from engine_wrapper import EngineWrapper, MultiEngineWrapper
from book_manager import BookManager
from test_engine import TestEngine
from hybrid_engine import AdaptiveHybridEngine, PositionAnalyzer

logger = logging.getLogger(__name__)

class ChessBot:
    """Ana satranç bot sınıfı"""
    
    def __init__(self, engine_name: str = "stockfish", use_hybrid: bool = True):
        self.engine_name = engine_name
        self.use_hybrid = use_hybrid
        self.engine_wrapper = None
        self.hybrid_engine = None
        self.book_manager = BookManager()
        self.test_engine = TestEngine()
        self.game_config = config.GAME_CONFIG
        
        # Logging ayarla
        self._setup_logging()
        
        # Motoru başlat
        self._initialize_engine()
    
    def _setup_logging(self):
        """Logging ayarlarını yapılandır"""
        log_config = config.LOGGING_CONFIG
        
        logging.basicConfig(
            level=getattr(logging, log_config["level"]),
            format=log_config["format"],
            handlers=[
                logging.FileHandler(log_config["file"]),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def _initialize_engine(self):
        """Motoru başlat"""
        try:
            if self.use_hybrid:
                self.hybrid_engine = AdaptiveHybridEngine()
                logger.info("Hibrit motor sistemi başlatıldı")
            else:
                self.engine_wrapper = EngineWrapper(self.engine_name)
                logger.info(f"Tek motor başlatıldı: {self.engine_name}")
        except Exception as e:
            logger.error(f"Motor başlatma hatası: {e}")
            raise
    
    def play_game(self, opponent_move: str = None, 
                  time_limit: float = None) -> Optional[chess.Move]:
        """Tek hamle oyna"""
        try:
            # Mevcut pozisyonu al (varsayılan başlangıç pozisyonu)
            board = chess.Board()
            
            # Eğer rakip hamlesi verilmişse uygula
            if opponent_move:
                try:
                    move = chess.Move.from_uci(opponent_move)
                    if move in board.legal_moves:
                        board.push(move)
                    else:
                        logger.error(f"Geçersiz hamle: {opponent_move}")
                        return None
                except ValueError:
                    logger.error(f"Geçersiz hamle formatı: {opponent_move}")
                    return None
            
            # En iyi hamleyi bul
            if self.use_hybrid and self.hybrid_engine:
                best_move = self.hybrid_engine.get_move(board, time_limit)
            else:
                best_move = self.engine_wrapper.get_move(board, time_limit)
            
            if best_move:
                logger.info(f"Hamle: {board.san(best_move)} ({best_move.uci()})")
                return best_move
            else:
                logger.warning("Hamle bulunamadı")
                return None
                
        except Exception as e:
            logger.error(f"Oyun hatası: {e}")
            return None
    
    def play_full_game(self, opponent_engine: str = None, 
                      max_moves: int = None) -> Dict[str, Any]:
        """Tam oyun oyna"""
        if max_moves is None:
            max_moves = self.game_config["max_moves"]
        
        board = chess.Board()
        moves = []
        game_info = {
            'result': None,
            'moves': [],
            'final_fen': None,
            'move_count': 0
        }
        
        try:
            # İkinci motor varsa başlat
            opponent_wrapper = None
            if opponent_engine:
                try:
                    opponent_wrapper = EngineWrapper(opponent_engine)
                except Exception as e:
                    logger.warning(f"Rakip motor başlatılamadı: {e}")
            
            move_count = 0
            while not board.is_game_over() and move_count < max_moves:
                # Sıra kimde?
                if board.turn == chess.WHITE:
                    # Beyaz (bizim bot)
                    if self.use_hybrid and self.hybrid_engine:
                        move = self.hybrid_engine.get_move(board)
                    else:
                        move = self.engine_wrapper.get_move(board)
                    player = "White"
                else:
                    # Siyah (rakip)
                    if opponent_wrapper:
                        move = opponent_wrapper.get_move(board)
                    else:
                        # Basit rastgele hamle
                        legal_moves = list(board.legal_moves)
                        if legal_moves:
                            move = legal_moves[0]  # İlk legal hamle
                        else:
                            break
                    player = "Black"
                
                if move:
                    san_move = board.san(move)
                    uci_move = move.uci()
                    
                    moves.append({
                        'move_number': move_count + 1,
                        'player': player,
                        'san': san_move,
                        'uci': uci_move,
                        'fen': board.fen()
                    })
                    
                    board.push(move)
                    move_count += 1
                    
                    logger.info(f"{move_count}. {player}: {san_move}")
                else:
                    logger.warning("Hamle bulunamadı")
                    break
            
            # Oyun sonucu
            if board.is_game_over():
                if board.is_checkmate():
                    if board.turn == chess.BLACK:
                        game_info['result'] = "1-0"  # Beyaz kazandı
                    else:
                        game_info['result'] = "0-1"  # Siyah kazandı
                elif board.is_stalemate():
                    game_info['result'] = "1/2-1/2"
                elif board.is_insufficient_material():
                    game_info['result'] = "1/2-1/2"
                elif board.is_fifty_moves():
                    game_info['result'] = "1/2-1/2"
                elif board.is_repetition():
                    game_info['result'] = "1/2-1/2"
            else:
                game_info['result'] = "*"  # Devam ediyor
            
            game_info['moves'] = moves
            game_info['final_fen'] = board.fen()
            game_info['move_count'] = move_count
            
            logger.info(f"Oyun tamamlandı: {game_info['result']}")
            
            # Rakip motoru kapat
            if opponent_wrapper:
                opponent_wrapper.close()
            
            return game_info
            
        except Exception as e:
            logger.error(f"Oyun hatası: {e}")
            return game_info
    
    def analyze_position(self, fen: str = None, depth: int = 20) -> Dict[str, Any]:
        """Pozisyonu analiz et"""
        try:
            if fen:
                board = chess.Board(fen)
            else:
                board = chess.Board()
            
            if self.use_hybrid and self.hybrid_engine:
                # Hibrit sistemle analiz
                analysis = self.hybrid_engine.controller.analyze_position_with_all_engines(board, depth)
                
                # Pozisyon tipini de analiz et
                position_analyzer = PositionAnalyzer()
                position_info = position_analyzer.analyze_position(board)
                
                # En iyi analizi seç
                best_analysis = {}
                best_score = -float('inf')
                
                for engine_name, engine_analysis in analysis.items():
                    if engine_analysis and 'score' in engine_analysis:
                        score = engine_analysis['score']
                        if score and hasattr(score, 'score') and score.score():
                            cp_score = score.score()
                            if abs(cp_score) > abs(best_score):
                                best_score = cp_score
                                best_analysis = engine_analysis
                
                if not best_analysis:
                    best_analysis = next(iter(analysis.values()), {})
                
                # Hibrit analiz sonucunu formatla
                formatted_analysis = {
                    'fen': board.fen(),
                    'evaluation': None,
                    'best_moves': [],
                    'depth': best_analysis.get('depth', 0),
                    'nodes': best_analysis.get('nodes', 0),
                    'time': best_analysis.get('time', 0),
                    'position_type': position_info['type'].value,
                    'confidence': position_info['confidence'],
                    'all_engines': analysis
                }
            else:
                analysis = self.engine_wrapper.analyze_position(board, depth)
                formatted_analysis = {
                    'fen': board.fen(),
                    'evaluation': None,
                    'best_moves': [],
                    'depth': analysis.get('depth', 0),
                    'nodes': analysis.get('nodes', 0),
                    'time': analysis.get('time', 0)
                }
            
            # Analiz sonuçlarını formatla (zaten yukarıda yapıldı)
            
            # Skoru formatla
            score = analysis.get('score', None)
            if score:
                if score.is_mate():
                    formatted_analysis['evaluation'] = f"M{score.mate()}"
                else:
                    cp = score.score()
                    if cp is not None:
                        formatted_analysis['evaluation'] = f"{cp/100:.2f}"
            
            # En iyi hamleleri formatla
            pv = analysis.get('pv', [])
            if pv:
                for i, move in enumerate(pv[:5]):  # İlk 5 hamle
                    formatted_analysis['best_moves'].append({
                        'rank': i + 1,
                        'move': board.san(move),
                        'uci': move.uci()
                    })
            
            return formatted_analysis
            
        except Exception as e:
            logger.error(f"Analiz hatası: {e}")
            return {}
    
    def create_book(self, pgn_files: list = None) -> Path:
        """Açılış kitabı oluştur"""
        try:
            logger.info("Açılış kitabı oluşturuluyor...")
            book_path = self.book_manager.create_anti_stockfish_book(pgn_files)
            logger.info(f"Kitap oluşturuldu: {book_path}")
            return book_path
        except Exception as e:
            logger.error(f"Kitap oluşturma hatası: {e}")
            raise
    
    def run_test(self, opponent: str = "stockfish", games: int = 100) -> Dict:
        """Test çalıştır"""
        try:
            logger.info(f"Test başlatılıyor: {self.engine_name} vs {opponent}")
            results = self.test_engine.run_comprehensive_test(
                opponent, self.engine_name, games
            )
            logger.info("Test tamamlandı")
            return results
        except Exception as e:
            logger.error(f"Test hatası: {e}")
            raise
    
    def interactive_mode(self):
        """İnteraktif mod"""
        print("Satranç Bot İnteraktif Modu")
        print("Komutlar:")
        print("  move <uci> - Hamle yap")
        print("  analyze [fen] - Pozisyonu analiz et")
        print("  game - Tam oyun oyna")
        print("  test - Test çalıştır")
        print("  book - Kitap oluştur")
        print("  quit - Çık")
        
        board = chess.Board()
        
        while True:
            try:
                command = input("\n> ").strip().lower()
                
                if command == "quit":
                    break
                elif command.startswith("move "):
                    uci_move = command[5:].strip()
                    move = self.play_game(uci_move)
                    if move:
                        board.push(move)
                        print(f"Hamle: {board.san(move)}")
                        print(f"Pozisyon: {board.fen()}")
                elif command.startswith("analyze"):
                    parts = command.split()
                    fen = parts[1] if len(parts) > 1 else None
                    analysis = self.analyze_position(fen)
                    if analysis:
                        print(f"Değerlendirme: {analysis.get('evaluation', 'N/A')}")
                        print(f"Derinlik: {analysis.get('depth', 0)}")
                        for move_info in analysis.get('best_moves', [])[:3]:
                            print(f"{move_info['rank']}. {move_info['move']}")
                elif command == "game":
                    game_info = self.play_full_game()
                    print(f"Oyun sonucu: {game_info['result']}")
                    print(f"Hamle sayısı: {game_info['move_count']}")
                elif command == "test":
                    games = int(input("Test oyun sayısı: ") or "10")
                    results = self.run_test(games=games)
                    print(f"Test tamamlandı: {results['results']['engine1_win_rate']:.2%}")
                elif command == "book":
                    self.create_book()
                    print("Kitap oluşturuldu")
                else:
                    print("Geçersiz komut")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Hata: {e}")
    
    def close(self):
        """Botu kapat"""
        if self.engine_wrapper:
            self.engine_wrapper.close()
        if self.hybrid_engine:
            self.hybrid_engine.close()
        logger.info("Bot kapatıldı")


def main():
    """Ana fonksiyon"""
    parser = argparse.ArgumentParser(description="Satranç Bot")
    parser.add_argument("--engine", default="stockfish", help="Motor adı")
    parser.add_argument("--hybrid", action="store_true", help="Hibrit motor sistemi kullan")
    parser.add_argument("--no-hybrid", action="store_true", help="Tek motor kullan")
    parser.add_argument("--mode", choices=["interactive", "game", "test", "book"], 
                       default="interactive", help="Çalışma modu")
    parser.add_argument("--opponent", default="stockfish", help="Rakip motor")
    parser.add_argument("--games", type=int, default=100, help="Test oyun sayısı")
    parser.add_argument("--move", help="Yapılacak hamle (UCI format)")
    parser.add_argument("--analyze", help="Analiz edilecek pozisyon (FEN)")
    
    args = parser.parse_args()
    
    try:
        use_hybrid = not args.no_hybrid  # Varsayılan olarak hibrit kullan
        if args.hybrid:
            use_hybrid = True
        
        bot = ChessBot(args.engine, use_hybrid=use_hybrid)
        
        if args.mode == "interactive":
            bot.interactive_mode()
        elif args.mode == "game":
            game_info = bot.play_full_game(args.opponent)
            print(f"Oyun sonucu: {game_info['result']}")
        elif args.mode == "test":
            results = bot.run_test(args.opponent, args.games)
            print(f"Test sonucu: {results['results']['engine1_win_rate']:.2%}")
        elif args.mode == "book":
            book_path = bot.create_book()
            print(f"Kitap oluşturuldu: {book_path}")
        
        if args.move:
            move = bot.play_game(args.move)
            if move:
                print(f"Hamle: {move.uci()}")
        
        if args.analyze:
            analysis = bot.analyze_position(args.analyze)
            print(f"Analiz: {analysis}")
        
    except Exception as e:
        logger.error(f"Ana hata: {e}")
        sys.exit(1)
    finally:
        if 'bot' in locals():
            bot.close()


if __name__ == "__main__":
    main()
