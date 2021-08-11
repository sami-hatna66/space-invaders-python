import sys
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import time
import random
import datetime

class GameThread(QThread):
    def __init__(self, Win):
        super(GameThread, self).__init__()
        self.Win = Win
        self.Flag = True

    def run(self):
        while self.Flag:
            self.Win.update()
            time.sleep(0.05)

    def stop(self):
        self.Flag = False
        self.quit()

class Bullet:
    def __init__(self, Position, Type):
        self.Position = [coord for coord in Position]
        self.Alive = True
        self.MoveBullet = BulletMovementThread(Position = self.Position[1], Type = Type)
        self.MoveBullet.DeadSignal.connect(self.KillBullet)
        self.MoveBullet.PosChanged.connect(self.PosChangedSlot)
        self.MoveBullet.start()

    def KillBullet(self):
        self.Alive = False

    def PosChangedSlot(self, NewPos):
        self.Position[1] = NewPos

class BulletMovementThread(QThread):
    PosChanged = pyqtSignal(int)
    DeadSignal = pyqtSignal()
    def __init__(self, Position, Type):
        super(BulletMovementThread, self).__init__()
        self.Position = Position
        self.Flag = True
        self.Type = Type

    def run(self):
        self.Step = 20
        while self.Flag:
            if self.Type == "Player":
                self.Position -= self.Step
            else:
                self.Position += self.Step
            time.sleep(0.05)
            if -20 <= self.Position <= 420:
                self.PosChanged.emit(self.Position)
            else:
                self.Stop()

    def Stop(self):
        self.Flag = False
        self.DeadSignal.emit()
        self.quit()

class Enemy:
    def __init__(self, Position, index):
        self.Position = Position
        self.Index = index
        self.DeadFlag = False
        self.BulletInstances = []
        self.BulletCounter = -1
        if self.Index[0] == 3 or self.Index[0] == 2:
           self.Value = 10
           self.Picture = QPixmap("Sprites/Enemy1.1.png")
        elif self.Index[0] == 1:
            self.Value = 20
            self.Picture = QPixmap("Sprites/Enemy2.1.png")
        else:
            self.Value = 30
            self.Picture = QPixmap("Sprites/Enemy3.1.png")

    def Die(self):
        self.DeadFlag = True
        self.Explode = Explosion(Frame1 = "Sprites/EnemyExplode1.png", Frame2 = "Sprites/EnemyExplode2.png", Frame3 = "Sprites/EnemyExplode3.png", Frame4 = "Sprites/EnemyExplode4.png")
        self.Explode.ChangePictureSignal.connect(self.ChangePictureExplosion)
        self.Explode.start()

    def ChangePictureExplosion(self, NewPic):
        self.Picture = NewPic


class Explosion(QThread):
    ChangePictureSignal = pyqtSignal(QPixmap)
    DoneSignal = pyqtSignal()
    def __init__(self, Frame1, Frame2, Frame3, Frame4):
        super(Explosion, self).__init__()
        self.Frame1 = Frame1
        self.Frame2 = Frame2
        self.Frame3 = Frame3
        self.Frame4 = Frame4

    def run(self):
        self.ChangePictureSignal.emit(QPixmap(self.Frame1))
        time.sleep(0.1)
        self.ChangePictureSignal.emit(QPixmap(self.Frame2))
        time.sleep(0.1)
        self.ChangePictureSignal.emit(QPixmap(self.Frame3))
        time.sleep(0.1)
        self.ChangePictureSignal.emit(QPixmap(self.Frame4))
        self.quit()
        time.sleep(0.5)
        self.DoneSignal.emit()

class Rocket(QObject):
    GameOverSignal = pyqtSignal(str)
    def __init__(self, Position):
        super(Rocket, self).__init__()
        self.Position = Position
        self.Direction = "Left"
        self.EnemyDirection = "Right"
        self.Picture = QPixmap("Sprites/Shooter1.png")
        self.MovingFlag = False
        self.ThreadInstances = 0
        self.BulletInstances = []
        self.BulletCounter = -1
        self.EnemyBulletInstances = []
        self.EnemyBulletCounter = -1
        self.EnemyBulletFlag = False
        self.BulletFlag = False
        self.EnemyInstances = []
        self.WhichEnemy = False
        self.Score = 0
        self.Lives = 3

    def SpawnEnemyBullet(self):
        Selector1 = random.randint(0, 3)
        Selector2 = random.randint(0, 9)
        if not self.EnemyInstances[Selector1][Selector2].DeadFlag:
            self.EnemyBulletInstances.append(Bullet(Position = [self.EnemyInstances[Selector1][Selector2].Position[0] + 15, self.EnemyInstances[Selector1][Selector2].Position[1]+ 30, 5, 5], Type = "Enemy"))
            self.EnemyBulletCounter += 1
            self.EnemyBulletFlag = True

    def SpawnBullet(self):
        self.BulletInstances.append(Bullet(Position = [self.Position[0] + 13, self.Position[1], 3, 20], Type = "Player"))
        self.BulletCounter += 1
        self.BulletFlag = True

    def MakeChecks(self):
        if len(self.BulletInstances) > 0:
            if not self.BulletInstances[self.BulletCounter].Alive:
                self.BulletFlag = False
            else:
                for enemylist in self.EnemyInstances:
                    for enemy in enemylist:
                        if self.BulletInstances[self.BulletCounter].Position[1] == enemy.Position[1] + 30 and enemy.Position[0] <= self.BulletInstances[self.BulletCounter].Position[0] <= enemy.Position[0] + 30 and enemy.DeadFlag == False:
                            self.Score += enemy.Value
                            enemy.Die()
                            self.BulletInstances[self.BulletCounter].KillBullet()
        if len(self.EnemyBulletInstances) > 0:
            if not self.EnemyBulletInstances[self.EnemyBulletCounter].Alive:
                self.EnemyBulletFlag = False
                self.SpawnEnemyBullet()
            else:
                if self.EnemyBulletInstances[self.EnemyBulletCounter].Position[1] == self.Position[1] and self.Position[0] <= self.EnemyBulletInstances[self.EnemyBulletCounter].Position[0] <= self.Position[0] + 30:
                    self.Lives -= 1
                    if self.Lives == 2:
                        self.Picture = QPixmap("Sprites/Shooter2.png")
                    elif self.Lives == 1:
                        self.Picture = QPixmap("Sprites/Shooter3.png")
                    elif self.Lives == 0:
                        self.Explode = Explosion(Frame1="Sprites/ShooterExplode1.png", Frame2="Sprites/ShooterExplode2.png", Frame3="Sprites/ShooterExplode3.png", Frame4="Sprites/ShooterExplode4.png")
                        self.Explode.ChangePictureSignal.connect(self.ChangePictureExplosion)
                        self.Explode.DoneSignal.connect(lambda: self.GameOverSignal.emit("Bad"))
                        self.Explode.start()
            AliveCounter = 0
            for enemylist in self.EnemyInstances:
                for enemy in enemylist:
                    if not enemy.DeadFlag:
                        AliveCounter += 1
                        self.Last = enemy
            if AliveCounter == 0:
                self.GameOverSignal.emit("Good")
            if self.Last.Position[1] >= 320:
                self.GameOverSignal.emit("Bad")

    def ChangePictureExplosion(self, NewPic):
        self.Picture = NewPic

    def Move(self):
        if self.ThreadInstances == 0:
            self.MoveThread = RocketMovementThread(Direction=self.Direction, Position=self.Position[0])
            self.ThreadInstances = 1
            self.MoveThread.start()
            self.MoveThread.PosChanged.connect(self.PosChangedSlot)

    def PosChangedSlot(self, NewPos):
        self.Position[0] = NewPos

    def StopMoving(self):
        self.MoveThread.stop()
        self.ThreadInstances = 0

    def SpawnEnemy(self):
        for x in range(0, 4):
            TempArray = [Enemy(Position=[(y * 40) + 100, (x * 40) + 20], index=[x, y]) for y in range(0, 10)]
            self.EnemyInstances.append(TempArray)
        self.MoveInX = MoveEnemies()
        self.MoveInX.Move.connect(self.ChangeEnemyPos)
        self.MoveInX.start()

    def ChangeEnemyPos(self):
        MoveDown = False
        if self.EnemyInstances[0][0].Position[0] <= 20:
            self.EnemyDirection = "Right"
            MoveDown = True
        elif self.EnemyInstances[0][9].Position[0] >= 545:
            self.EnemyDirection = "Left"
            MoveDown = True
        for enemylist in self.EnemyInstances:
            for enemy in enemylist:
                if MoveDown:
                    enemy.Position[1] += 20
                if self.EnemyDirection == "Left":
                    enemy.Position[0] -= 5
                else:
                    enemy.Position[0] += 5
        for enemylist in self.EnemyInstances:
            for enemy in enemylist:
                if not enemy.DeadFlag:
                    if self.WhichEnemy:
                        if enemy.Index[0] == 3 or enemy.Index[0] == 2:
                            enemy.Picture = QPixmap("Sprites/Enemy1.1.png")
                        elif enemy.Index[0] == 1:
                            enemy.Picture = QPixmap("Sprites/Enemy2.1.png")
                        else:
                            enemy.Picture = QPixmap("Sprites/Enemy3.1.png")
                    else:
                        if enemy.Index[0] == 3 or enemy.Index[0] == 2:
                            enemy.Picture = QPixmap("Sprites/Enemy1.2.png")
                        elif enemy.Index[0] == 1:
                            enemy.Picture = QPixmap("Sprites/Enemy2.2.png")
                        else:
                            enemy.Picture = QPixmap("Sprites/Enemy3.2.png")
        self.WhichEnemy = not self.WhichEnemy

class MoveEnemies(QThread):
    Move = pyqtSignal()
    def run(self):
        while True:
            time.sleep(0.5)
            self.Move.emit()

class RocketMovementThread(QThread):
    PosChanged = pyqtSignal(int)
    def __init__(self, Direction, Position):
        super(RocketMovementThread, self).__init__()
        self.Direction = Direction
        self.Position = Position
        self.Flag = True

    def run(self):
        self.Step = 10
        while self.Flag:
            if self.Direction == "Left":
                self.Position -= self.Step
            else:
                self.Position += self.Step
            time.sleep(0.05)
            if 0 <= self.Position <= 570:
                self.PosChanged.emit(self.Position)

    def stop(self):
        self.Flag = False
        self.quit()

class Window(QMainWindow):
    def __init__(self):
        super(Window, self).__init__()
        self.show()
        self.setFixedSize(600, 400)

        self.IsGameOver = False

        self.setStyleSheet("background-color: black;")
        self.StartGame()

    def StartGame(self):
        self.StartTime = datetime.datetime.now()
        self.MainGameThread = GameThread(Win=self)
        self.MainGameThread.start()
        self.Rocket1 = Rocket(Position = [285, 350])
        self.Rocket1.GameOverSignal.connect(self.GameOver)
        self.Rocket1.SpawnEnemy()
        self.Rocket1.SpawnEnemyBullet()

    def keyPressEvent(self, QKeyEvent):
        if not self.IsGameOver:
            if QKeyEvent.key() == Qt.Key_Left and not QKeyEvent.isAutoRepeat():
                self.Rocket1.Direction = "Left"
                self.Rocket1.Move()
            elif QKeyEvent.key() == Qt.Key_Right and not QKeyEvent.isAutoRepeat():
                self.Rocket1.Direction = "Right"
                self.Rocket1.Move()
            elif QKeyEvent.isAutoRepeat():
                pass
        else:
            if QKeyEvent.key() == Qt.Key_Space:
                self.StartGame()
                self.IsGameOver = False

    def GameOver(self, Type):
        self.GameTime = datetime.datetime.now() - self.StartTime
        self.MainGameThread.stop()
        self.IsGameOver = True
        self.Type = Type
        self.update()

    def keyReleaseEvent(self, QKeyEvent):
        if QKeyEvent.key() == Qt.Key_Left or QKeyEvent.key() == Qt.Key_Right:
            self.Rocket1.StopMoving()
        elif QKeyEvent.key() == Qt.Key_Space:
            if not self.Rocket1.BulletFlag:
                self.Rocket1.SpawnBullet()

    def paintEvent(self, QPaintEvent):
        Painter = QPainter()
        Painter.begin(self)
        if not self.IsGameOver:
            Painter.setBrush(QBrush(QColor(30, 177, 0)))
            Painter.setPen(Qt.black)
            if len(self.Rocket1.BulletInstances) > 0:
                if self.Rocket1.BulletFlag:
                    Painter.drawRect(self.Rocket1.BulletInstances[self.Rocket1.BulletCounter].Position[0], self.Rocket1.BulletInstances[self.Rocket1.BulletCounter].Position[1], self.Rocket1.BulletInstances[self.Rocket1.BulletCounter].Position[2], self.Rocket1.BulletInstances[self.Rocket1.BulletCounter].Position[3])
            Painter.drawPixmap(self.Rocket1.Position[0], self.Rocket1.Position[1], self.Rocket1.Picture)
            self.Rocket1.MakeChecks()
            for enemylist in self.Rocket1.EnemyInstances:
                for enemy in enemylist:
                    Painter.drawPixmap(enemy.Position[0], enemy.Position[1], enemy.Picture)
            Painter.setPen(QPen(QColor(30, 177, 0)))
            Painter.setFont(QFont("minecraft", 15))
            Painter.drawText(5, 15, "score: " + str(self.Rocket1.Score))
            Painter.drawText(100, 15, "lives: " + str(self.Rocket1.Lives))
            if len(self.Rocket1.EnemyBulletInstances) > 0:
                Painter.drawEllipse(self.Rocket1.EnemyBulletInstances[self.Rocket1.EnemyBulletCounter].Position[0], self.Rocket1.EnemyBulletInstances[self.Rocket1.EnemyBulletCounter].Position[1], self.Rocket1.EnemyBulletInstances[self.Rocket1.EnemyBulletCounter].Position[2], self.Rocket1.EnemyBulletInstances[self.Rocket1.EnemyBulletCounter].Position[3])
        else:
            Painter.setPen(QPen(QColor(30, 177, 0)))
            Painter.setFont(QFont("minecraft", 30))
            if self.Type == "Bad":
                Painter.drawText(210, 180, "GAME OVER")
            else:
                Painter.drawText(210, 180, "VICTORY")
            Painter.setFont(QFont("minecraft", 15))
            Painter.drawText(210, 210, "Score: " + str(self.Rocket1.Score))
            Painter.drawText(210, 230, "Time: " + str(self.GameTime))
            Painter.drawText(210, 250, "Press <Space> to play again")
        Painter.end()

    def closeEvent(self, QCloseEvent):
        self.MainGameThread.stop()

def main():
    App = QApplication(sys.argv)
    Root = Window()
    sys.exit(App.exec())

if __name__ == "__main__":
    main()