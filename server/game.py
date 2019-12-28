import json
import random
from collections import defaultdict
#all_words = json.load(open("words_dictionary.json"))
all_words = {}
with open("corncob_lowercase.txt") as f:
    for row in f:
        all_words[row.strip()] = 1
words_by_letters = defaultdict(list)
for word in all_words.keys():
    words_by_letters[len(word)].append(word)

ROUND_TIME = 30
LOCK_TIME = 3
NEW_ROUND_TIME = 1

MAX_Y_OFFSET_FOR_WORD = 0.1
MAX_X_OFFSET_FOR_LETTERS = 0.2

class Game:
    def __init__(self):
        self.max_players = 5
        self.round_num = 0
        self.score = 0
        self.round_word = ""
        self.round_time = ROUND_TIME
        self.state = "waiting"
        self.validation_boxes = []
        self.players = []
        self.lock_time = 0
        self.new_round_timer = 0
        self.victory_words = []

    def serialize(self):
        s = {
            'round_time':self.round_time,
            'lock_time':self.lock_time,
            'state':self.state,
            'players':[p.serialize() for p in self.players],
            'validation_boxes':self.validation_boxes,
            'score':self.score,
            'victory_words':", ".join(self.victory_words)
        }
        return s

    def status_str(self):
        word = self.round_word
        if self.state != 'playing':
            word = "..."
        return "round %d, score=%d, word = \"%s\", %d/%d players" % (
            self.round_num, self.score, word,
            len(self.players), self.max_players
        )

    def check_valid_word(self):
        ltr_players = list(self.players)
        ltr_players.sort(key=lambda p:p.x)
        
        def new_row(player):
            return [player]

        def row_middle(row):
            return sum([p.y for p in row]) / len(row)

        rows = [new_row(ltr_players[0])]

        for player in ltr_players[1:]:
            best_row = None
            best_row_y = 99999999
            for row in rows:
                my = row_middle(row)
                dy = abs(my-player.y)
                if dy < best_row_y:
                    if player.x < row[-1].x + MAX_X_OFFSET_FOR_LETTERS:
                        best_row_y = dy
                        best_row = row
            if best_row and best_row_y < MAX_Y_OFFSET_FOR_WORD:
                best_row.append(player)
            else:
                rows.append(new_row(player))

        best_word_length = 0
        best_word = None
        self.validation_boxes = []
        for row in rows:
            x1 = row[0].x
            x2 = row[-1].x
            y1 = min([r.y for r in row])
            y2 = max([r.y for r in row])
            word = "".join([r.symbol for r in row])
            if len(word) > 1:
                valid = False
                if word in all_words:
                    valid = True
                    if len(word) > best_word_length:
                        best_word = word
                        best_word_length = len(word)
                self.validation_boxes.append({
                    'x1':x1, 'x2':x2, 'y1':y1, 'y2':y2, 'valid':valid
                })
            
            
        return best_word

    def win(self):
        self.state = "victory"
        self.new_round_timer = NEW_ROUND_TIME

    def lose(self):
        self.state = "defeat"
        self.new_round_timer = NEW_ROUND_TIME
        self.round_num = 0
        self.score = 0
        self.victory_words = []

    def new_round(self):
        self.round_num += 1
        self.state = "playing"
        self.round_time = ROUND_TIME
        self.lock_time = 0
        possible_words = words_by_letters[len(self.players)]
        chosen_word = list(random.choice(possible_words))
        self.round_word = "".join(chosen_word)
        random.shuffle(chosen_word)
        for s,p in zip(chosen_word, self.players):
            p.symbol = s
            p.x = random.random()
            p.y = random.random()
            p.tx = p.x
            p.ty = p.y

    def add_player(self, player):
        self.players.append(player)
        player.symbol = "?"

    def update(self, delta_time):
        for player in self.players:
            player.update(delta_time)

        if self.state == "playing":
            self.update_playing(delta_time)

        if self.state in ['victory', 'defeat']:
            self.new_round_timer -= delta_time
            if self.new_round_timer <= 0:
                self.new_round()

    def update_playing(self, delta_time):
        best_word = self.check_valid_word()
        if best_word:
            self.lock_time += delta_time
        else:
            self.lock_time = 0

        self.round_time -= delta_time

        if best_word:
            if self.lock_time > LOCK_TIME or self.round_time <= 0:
                if len(best_word) == len(self.players):
                    self.score += 10
                else:
                    self.score += 1
                self.victory_words.append(best_word)
                self.win()
        else:
            if self.round_time <= 0:
                self.lose()
    