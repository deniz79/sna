#!/usr/bin/env python3
"""
Basit Sürpriz Açılış Kitabı Oluşturucu
"""

import chess
import chess.pgn
import random
from pathlib import Path

def create_surprise_openings():
    """Sürpriz açılışlar oluştur"""
    
    # Stockfish'in zorlandığı açılışlar
    surprise_openings = [
        # King's Indian Defense
        ["d4", "Nf6", "c4", "g6", "Nc3", "Bg7", "e4", "d6"],
        
        # Benoni Defense
        ["d4", "Nf6", "c4", "c5", "d5", "e6", "Nc3", "exd5", "cxd5", "d6"],
        
        # Modern Defense
        ["e4", "g6", "d4", "Bg7", "Nc3", "d6"],
        
        # Pirc Defense
        ["e4", "d6", "d4", "Nf6", "Nc3", "g6"],
        
        # Alekhine Defense
        ["e4", "Nf6", "e5", "Nd5", "d4", "d6", "Nf3", "dxe5", "Nxe5"],
        
        # Scandinavian Defense
        ["e4", "d5", "exd5", "Qxd5", "Nc3", "Qa5"],
        
        # Latvian Gambit
        ["e4", "e5", "Nf3", "f5"],
        
        # Elephant Gambit
        ["e4", "e5", "Nf3", "d5"],
        
        # Englund Gambit
        ["d4", "e5"],
        
        # Budapest Gambit
        ["d4", "Nf6", "c4", "e5"],
        
        # Grob's Attack
        ["g4", "d5", "Bg2", "Bxg4", "c4", "c6"],
        
        # Polish Opening
        ["b4", "e5", "Bb2", "Bxb4", "Bxe5", "Nf6"],
        
        # Sokolsky Opening
        ["b4", "e5", "Bb2", "Bxb4", "Bxe5", "Nf6", "e3"],
        
        # Bird's Opening
        ["f4", "d5", "Nf3", "Nf6", "e3", "g6"],
        
        # Dutch Defense
        ["d4", "f5", "g3", "Nf6", "Bg2", "e6", "Nf3", "Be7"],
        
        # Nimzo-Indian Defense
        ["d4", "Nf6", "c4", "e6", "Nc3", "Bb4", "Qc2", "c5"],
        
        # Grünfeld Defense
        ["d4", "Nf6", "c4", "g6", "Nc3", "d5", "cxd5", "Nxd5"],
        
        # King's Indian Attack
        ["Nf3", "d5", "g3", "Bg4", "Bg2", "Nd7", "O-O", "e6"],
        
        # Reti Opening
        ["Nf3", "d5", "c4", "c6", "b3", "Bg4", "g3", "Nf6"],
        
        # Catalan Opening
        ["d4", "Nf6", "c4", "e6", "g3", "d5", "Bg2", "dxc4"],
        
        # Trompowsky Attack
        ["d4", "Nf6", "Bg5", "Ne4", "Bf4", "c5", "f3", "Qa5"]
    ]
    
    games = []
    
    for i, opening_moves in enumerate(surprise_openings):
        # Her açılış için 3 farklı varyant oluştur
        for variation in range(3):
            game = chess.pgn.Game()
            game.headers["Event"] = f"Anti-Stockfish Opening {i+1}"
            game.headers["White"] = "Anti-Stockfish Bot"
            game.headers["Black"] = "Stockfish"
            game.headers["Result"] = "1-0"
            
            board = game.board()
            
            # Temel açılışı oyna
            for move_san in opening_moves:
                try:
                    move = board.parse_san(move_san)
                    if move in board.legal_moves:
                        board.push(move)
                        game.add_main_variation(move)
                    else:
                        break
                except:
                    break
            
            # 3-5 ek hamle ekle
            extra_moves = random.randint(3, 5)
            for _ in range(extra_moves):
                legal_moves = list(board.legal_moves)
                if legal_moves and not board.is_game_over():
                    move = random.choice(legal_moves)
                    board.push(move)
                    game.add_main_variation(move)
                else:
                    break
            
            games.append(game)
    
    return games

def save_pgn_games(games, filename):
    """Oyunları PGN dosyasına kaydet"""
    pgn_file = Path("data/pgn") / filename
    pgn_file.parent.mkdir(exist_ok=True)
    
    with open(pgn_file, 'w') as f:
        for game in games:
            f.write(str(game) + "\n\n")
    
    print(f"PGN dosyası kaydedildi: {pgn_file}")
    return pgn_file

def main():
    """Ana fonksiyon"""
    print("🎯 Basit Sürpriz Açılış Kitabı Oluşturucu")
    print("=" * 50)
    
    # Sürpriz açılışları oluştur
    games = create_surprise_openings()
    print(f"✅ {len(games)} sürpriz açılış oluşturuldu")
    
    # PGN dosyasına kaydet
    pgn_file = save_pgn_games(games, "surprise_openings.pgn")
    
    print(f"\n📚 Oluşturulan açılışlar:")
    for i, opening in enumerate([
        "King's Indian Defense", "Benoni Defense", "Modern Defense", 
        "Pirc Defense", "Alekhine Defense", "Scandinavian Defense",
        "Latvian Gambit", "Elephant Gambit", "Englund Gambit", 
        "Budapest Gambit", "Grob's Attack", "Polish Opening",
        "Sokolsky Opening", "Bird's Opening", "Dutch Defense",
        "Nimzo-Indian Defense", "Grünfeld Defense", "King's Indian Attack",
        "Reti Opening", "Catalan Opening", "Trompowsky Attack"
    ]):
        print(f"  {i+1}. {opening}")
    
    print(f"\n🎮 Kullanım:")
    print(f"  python3 main.py --hybrid --book {pgn_file}")

if __name__ == "__main__":
    main()
