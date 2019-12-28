import random
import math

SPEED = 0.3

class Player:
    def __init__(self, pid):
        self.pid = pid
        self.x = random.random()
        self.y = random.random()
        self.tx = self.x
        self.ty = self.y
        self.symbol = ""
        self.in_play = False
    
    def update(self, delta_time):
        dx = self.tx - self.x
        dy = self.ty - self.y
        dist = math.sqrt(dx**2 + dy**2)
        if dist < delta_time * SPEED:
            self.x = self.tx
            self.y = self.ty
        else:
            self.x += dx / dist * delta_time * SPEED
            self.y += dy / dist * delta_time * SPEED

    def serialize(self):
        return {
            'x':self.x, 'y':self.y,
            'tx':self.tx, 'ty':self.ty,
            'pid':self.pid,
            'symbol':self.symbol,
            'in_play':self.in_play,
        }