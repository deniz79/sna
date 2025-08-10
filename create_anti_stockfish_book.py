#!/usr/bin/env python3
"""
Stockfish'e Karşı Sürpriz Açılış Kitabı Oluşturucu
"""

import chess
import chess.pgn
import subprocess
import requests
import gzip
import logging
from pathlib import Path
from typing import List, Dict, Set
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AntiStockfishBookCreator:
    """Stockfish'e karşı özel kitap oluşturucu"""
    
    def __init__(self):
        self.data_dir = Path("data")
        self.pgn_dir = self.data_dir / "pgn"
        self.books_dir = self.data_dir / "books"
        self.pgn_dir.mkdir(exist_ok=True)
        self.books_dir.mkdir(exist_ok=True)
        
        # Stockfish'in zorlandığı açılışlar
        self.anti_stockfish_openings = {
            "King's Indian Defense": ["d4", "Nf6", "c4", "g6", "Nc3", "Bg7", "e4", "d6"],
            "Benoni Defense": ["d4", "Nf6", "c4", "c5", "d5", "e6", "Nc3", "exd5", "cxd5", "d6"],
            "Modern Defense": ["e4", "g6", "d4", "Bg7", "Nc3", "d6"],
            "Pirc Defense": ["e4", "d6", "d4", "Nf6", "Nc3", "g6"],
            "Alekhine Defense": ["e4", "Nf6", "e5", "Nd5", "d4", "d6", "Nf3", "dxe5", "Nxe5"],
            "Scandinavian Defense": ["e4", "d5", "exd5", "Qxd5", "Nc3", "Qa5"],
            "Latvian Gambit": ["e4", "e5", "Nf3", "f5"],
            "Elephant Gambit": ["e4", "e5", "Nf3", "d5"],
            "Englund Gambit": ["d4", "e5"],
            "Budapest Gambit": ["d4", "Nf6", "c4", "e5"]
        }
    
    def download_lichess_games(self, year: int = 2023, month: int = 1, max_games: int = 10000):
        """Lichess veritabanından oyunları indir"""
        url = f"https://database.lichess.org/standard/lichess_db_standard_rated_{year}-{month:02d}.pgn.zst"
        filename = f"lichess_{year}_{month:02d}.pgn.zst"
        filepath = self.pgn_dir / filename
        
        if not filepath.exists():
            logger.info(f"Lichess veritabanı indiriliyor: {url}")
            try:
                response = requests.get(url, stream=True)
                response.raise_for_status()
                
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                logger.info(f"Veritabanı indirildi: {filepath}")
            except Exception as e:
                logger.error(f"İndirme hatası: {e}")
                return None
        
        return filepath
    
    def extract_anti_stockfish_games(self, pgn_file: Path, max_games: int = 1000) -> List[chess.pgn.Game]:
        """Stockfish'e karşı kazanılmış oyunları çıkar"""
        games = []
        stockfish_losses = 0
        
        logger.info(f"Anti-Stockfish oyunları çıkarılıyor: {pgn_file}")
        
        try:
            with open(pgn_file, 'r', encoding='utf-8') as f:
                game_count = 0
                
                while game_count < max_games:
                    try:
                        game = chess.pgn.read_game(f)
                        if game is None:
                            break
                        
                        # Stockfish'e karşı kazanılmış oyunları filtrele
                        if self._is_stockfish_loss(game):
                            stockfish_losses += 1
                            
                            # İlk 15 hamleyi al (açılış odaklı)
                            moves = list(game.mainline_moves())
                            if len(moves) >= 10 and len(moves) <= 50:
                                games.append(game)
                                game_count += 1
                                
                                if game_count % 100 == 0:
                                    logger.info(f"{game_count} oyun işlendi...")
                        
                    except Exception as e:
                        continue
            
            logger.info(f"Toplam {len(games)} anti-Stockfish oyunu bulundu")
            return games
            
        except Exception as e:
            logger.error(f"Oyun çıkarma hatası: {e}")
            return []
    
    def _is_stockfish_loss(self, game: chess.pgn.Game) -> bool:
        """Oyunun Stockfish'e karşı kayıp olup olmadığını kontrol et"""
        try:
            # Oyun sonucu
            result = game.headers.get("Result", "")
            if result not in ["1-0", "0-1"]:
                return False
            
            # Oyuncu isimleri
            white = game.headers.get("White", "").lower()
            black = game.headers.get("Black", "").lower()
            
            # Stockfish isimlerini kontrol et
            stockfish_names = ["stockfish", "sf", "stockfish-dev"]
            
            # Stockfish'in hangi renkte olduğunu bul
            stockfish_color = None
            if any(name in white for name in stockfish_names):
                stockfish_color = chess.WHITE
            elif any(name in black for name in stockfish_names):
                stockfish_color = chess.BLACK
            else:
                return False
            
            # Stockfish kaybetti mi?
            if stockfish_color == chess.WHITE and result == "0-1":
                return True
            elif stockfish_color == chess.BLACK and result == "1-0":
                return True
            
            return False
            
        except Exception as e:
            return False
    
    def create_surprise_variations(self) -> List[chess.pgn.Game]:
        """Sürpriz varyantlar oluştur"""
        games = []
        
        logger.info("Sürpriz varyantlar oluşturuluyor...")
        
        for opening_name, moves in self.anti_stockfish_openings.items():
            # Her varyant için 5 farklı devam oluştur
            for variation in range(5):
                game = chess.pgn.Game()
                game.headers["Event"] = f"Anti-Stockfish {opening_name}"
                game.headers["White"] = "Anti-Stockfish Bot"
                game.headers["Black"] = "Stockfish"
                game.headers["Result"] = "1-0"
                
                board = game.board()
                
                # Temel açılışı oyna
                for i, move_san in enumerate(moves):
                    try:
                        move = board.parse_san(move_san)
                        board.push(move)
                        game.add_main_variation(move)
                    except:
                        break
                
                # Rastgele devam hamleleri ekle (5-10 hamle)
                extra_moves = random.randint(5, 10)
                for _ in range(extra_moves):
                    legal_moves = list(board.legal_moves)
                    if legal_moves:
                        move = random.choice(legal_moves)
                        board.push(move)
                        game.add_main_variation(move)
                    else:
                        break
                
                # Oyunu tamamla
                if not board.is_game_over():
                    game.headers["Result"] = "*"  # Devam ediyor
                else:
                    game.headers["Result"] = board.result()
                
                games.append(game)
        
        logger.info(f"{len(games)} sürpriz varyant oluşturuldu")
        return games
    
    def create_polyglot_book(self, games: List[chess.pgn.Game], output_name: str = "anti_stockfish.bin"):
        """Polyglot kitap oluştur"""
        if not games:
            logger.error("Oyun listesi boş!")
            return None
        
        # Geçici PGN dosyası oluştur
        temp_pgn = self.pgn_dir / "temp_anti_stockfish.pgn"
        
        logger.info(f"Geçici PGN dosyası oluşturuluyor: {temp_pgn}")
        
        with open(temp_pgn, 'w', encoding='utf-8') as f:
            for game in games:
                f.write(str(game) + "\n\n")
        
        # Polyglot komutu
        output_path = self.books_dir / output_name
        cmd = [
            "polyglot", "make-book",
            "-pgn", str(temp_pgn),
            "-bin", str(output_path),
            "-min-game", "1",      # En az 1 oyun
            "-max-ply", "20",      # İlk 20 hamle
            "-min-score", "0",     # Minimum skor
            "-max-score", "100",   # Maksimum skor
            "-random", "0"         # Rastgele değil, ağırlıklı
        ]
        
        logger.info(f"Polyglot kitap oluşturuluyor: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info(f"Kitap oluşturuldu: {output_path}")
            
            # Geçici dosyayı sil
            temp_pgn.unlink()
            
            return output_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Polyglot hatası: {e.stderr}")
            return None
        except Exception as e:
            logger.error(f"Kitap oluşturma hatası: {e}")
            return None
    
    def create_aggressive_book(self) -> Path:
        """Agresif açılış kitabı oluştur"""
        logger.info("Agresif açılış kitabı oluşturuluyor...")
        
        # 1. Sürpriz varyantlar oluştur
        surprise_games = self.create_surprise_variations()
        
        # 2. Lichess'ten anti-Stockfish oyunları indir (opsiyonel)
        lichess_games = []
        try:
            pgn_file = self.download_lichess_games(2023, 1, 1000)
            if pgn_file:
                lichess_games = self.extract_anti_stockfish_games(pgn_file, 500)
        except Exception as e:
            logger.warning(f"Lichess oyunları indirilemedi: {e}")
        
        # 3. Tüm oyunları birleştir
        all_games = surprise_games + lichess_games
        
        # 4. Polyglot kitap oluştur
        book_path = self.create_polyglot_book(all_games, "aggressive_anti_stockfish.bin")
        
        if book_path:
            logger.info(f"Agresif kitap oluşturuldu: {book_path}")
            
            # Kitap istatistiklerini göster
            self._show_book_stats(book_path)
        
        return book_path
    
    def _show_book_stats(self, book_path: Path):
        """Kitap istatistiklerini göster"""
        try:
            import chess.polyglot
            
            reader = chess.polyglot.open_reader(book_path)
            entries = list(reader)
            
            logger.info(f"Kitap istatistikleri:")
            logger.info(f"  Toplam entry: {len(entries)}")
            
            # En popüler hamleleri göster
            move_counts = {}
            for entry in entries:
                move_uci = entry.move.uci()
                move_counts[move_uci] = move_counts.get(move_uci, 0) + 1
            
            # En popüler 10 hamle
            top_moves = sorted(move_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            logger.info("  En popüler hamleler:")
            for move, count in top_moves:
                logger.info(f"    {move}: {count} kez")
            
            reader.close()
            
        except Exception as e:
            logger.error(f"Kitap istatistikleri hatası: {e}")

def main():
    """Ana fonksiyon"""
    creator = AntiStockfishBookCreator()
    
    print("🎯 Stockfish'e Karşı Sürpriz Açılış Kitabı Oluşturucu")
    print("=" * 60)
    
    # Agresif kitap oluştur
    book_path = creator.create_aggressive_book()
    
    if book_path:
        print(f"\n✅ Kitap başarıyla oluşturuldu: {book_path}")
        print("\n📚 Bu kitap şu açılışları içerir:")
        for opening in creator.anti_stockfish_openings.keys():
            print(f"  • {opening}")
        
        print("\n🎮 Kullanım:")
        print(f"  python3 main.py --hybrid --book {book_path}")
    else:
        print("\n❌ Kitap oluşturulamadı!")

if __name__ == "__main__":
    main()
