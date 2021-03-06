""" Checkers Logic"""

# Import Qt module
from copy import deepcopy

from PyQt5.QtCore import QCoreApplication
import Board
import Piece
import TypeMove
import Encoder
import Sender

import json
import pika


class Checkers:
    """
        default constructor creates the board and populates
        the board with pieces
    """
    def __init__(self, *args, **kwargs):
        if len(kwargs) is 0:
            self.board = Board(8)
            self.size = self.board.getSize()
            self.turn = 0
            self.best_move = None
            self.game_over = False
            self.jumpAgain = (False,None,None)
        else:
            self.board = kwargs['board']
            self.size = kwargs['size']
            self.turn = kwargs['turn']
            self.best_move = kwargs['best_move']
            self.game_over = kwargs['game_over']
            self.jumpAgain = kwargs['jumpAgain']

    def __json__(self):
        return {'board': json.dumps(self.board, cls=Encoder.Encoder), 'size': self.size, 'turn': self.turn, 'best_move': self.best_move,
                'game_over': self.game_over, 'jump_again': self.jumpAgain, 'p': json.dumps(self.p, cls=Encoder.Encoder)}

    class Factory:
        @staticmethod
        def create(board, size, turn, best_move, game_over, jumpAgain):
            return Checkers(board=board, size=size, turn=turn,
                            best_move=best_move, game_over=game_over,
                            jumpAgain=jumpAgain)
    """
         gets if any of the players pieces can jump and adds it to
         the array, and returns it
    """
    def forceJump(self,player):
        moves = []
        for i in range (self.size):
            for j in range (self.size):
                tmp = self.board.getPieceAt(i, j)
                # checks if tmp is not none and player == the piece
                if tmp and player == tmp.getOwner() :
                    jumpF = self.canJump(i, j)
                    # if jumpF array is not empty append i , j and each value in the array
                    # for that piece
                    if jumpF :
                        for n in jumpF:
                            moves.append(n)
        return moves

    # returns if the game is over
    def isOver(self):
        return self.game_over

    # checks to see if the game has ended and sets game_over to true
    def checkWin(self, typeMove):
        if self.board.countPlayerPieces ==0 or len(self.getMoves("Player")) == 0:
            self.game_over = True
            return "AI"
        elif self.board.countAiPieces ==0 or len(self.getMoves("AI")) == 0:
            self.game_over = True
            return "Player"

    """
        validates if piece at X,Y can move to x1 , y1
        checks if x1 and y1 is inside the board and x1 and y1 is a empty space
        returns true or false
    """
    def validMove(self,x1,y1):
        if self.board.getSize() > x1 >= 0 and 0 <= y1 < self.board.getSize():
            if not self.board.pieceAt(x1, y1):
                return True
        else:
            return False

    def sendAndMove(self, player, x, y, x1, y1):
        # Lock.startTurn(self)
        #print(str(player) + str(x) + "," + str(y) + "," + str(x1) + "," + str(y1))
        pos1 = Sender.Sender.reformat(x, y)
        pos2 = Sender.Sender.reformat(x1, y1)
        data = Sender.Sender.move(pos1, pos2)
        self.send(data)
        # sending
        # Sender.move(self, Sender.reformat(self,x,y), Sender.reformat(self,x1,y1))
        # time.sleep(4)
        # Lock.endTurn(self)


    def sendAndRemove(self, player, removePieceX, removePieceY):
        # Lock.startTurn(self)

        removePiece = Sender.Sender.reformat(removePieceX, removePieceY)
        data = Sender.Sender.remove(removePiece)
        self.send(data)
        # sending
        # if player is "AI":
        #     Sender.remove_AIs(self, Sender.reformat(self,removePieceX, removePieceY))
        # else: Sender.remove_player(self, Sender.reformat(self,removePieceX, removePieceY))
        # time.sleep(4)
        # Lock.endTurn(self)
    def send(self, data):
        uname = "admin"
        password = "password"
        info = pika.PlainCredentials(uname, password)
        connection = pika.BlockingConnection(pika.ConnectionParameters(
            'localhost', credentials = info))
        channel = connection.channel()

        channel.queue_declare(queue='for_robot')
        channel.basic_publish(exchange='',
                              routing_key='for_robot',
                              body=data)
        connection.close()

    # moves a piece players piece from X Y to x1 y1
    def movePiece(self,player,x,y,x1,y1,typeMove):



        #self.sender = Sender#

        moved = False
        #gets an array of movable positions x y given by user
        moves = self.getMoves(player)
        # move is the string of x y, x1 y1 for comparing to the array of movable positions
        move = str(x)+","+str(y)+","+str(x1)+","+str(y1)
        if not self.isOver() :
            if self.forceJump(player):
                #Second jump
                if self.jumpAgain[0]:
                    # if jumpagain is true get the jumpable moves for jumpAgain[1], jumpAgain[2]
                    moves = self.canJump(self.jumpAgain[1], self.jumpAgain[2])

                    #compares moves to move if equal move the piece and remove the piece being jumped
                    for i in moves:
                        if i == move:
                            self.board.movePiece(x, y, x1, y1)
                            if (typeMove == TypeMove.TypeMove.real):
                                self.sendAndMove(player, x, y, x1, y1)
                            # checks if a jump is true then remove the piece being jumped

                            removePieceX = (x + (x1))/2
                            removePieceY = (y + (y1))/2

                            if (typeMove == TypeMove.TypeMove.real):
                                self.sendAndRemove(player, removePieceX, removePieceY)

                            self.board.removePiece(removePieceX, removePieceY)

                            #checks if it is king
                            if self.isKing(x1,y1):
                                self.board.updatePieceType(1,x1,y1)

                            #checks if it can jump again sets jumpAgain to true if true else set to False
                            if self.canJump(x1, y1):
                                moved = False
                                self.jumpAgain=(True,x1,y1)
                                break
                            else:
                                self.jumpAgain=(False,None,None)
                                moved = True
                                break

                else:
                    # This is the first jump
                    for i in moves:
                        if i == move :

                            if (typeMove == TypeMove.TypeMove.real):
                                self.sendAndMove(player, x, y, x1, y1)

                            self.board.movePiece(x, y, x1, y1)
                            # checks if a jump is true then remove the piece being jumped
                            removePieceX = (x + (x1))/2
                            removePieceY = (y + (y1))/2

                            if (typeMove == TypeMove.TypeMove.real):
                                self.sendAndRemove(player, removePieceX, removePieceY)

                            self.board.removePiece(removePieceX, removePieceY)
                            #after jumping check if it can be Kinged and can it jump again
                            if self.isKing(x1,y1):
                                self.board.updatePieceType(1,x1,y1)

                            if self.canJump(x1, y1):
                                moved = False
                                self.jumpAgain= (True,x1,y1)
                                break
                            else:
                                self.jumpAgain= (False,None,None)
                                moved = True
                                break
            else:
            # checks if the input equals any possible moves
                if moves:
                    for i in moves:
                        if(i == move):

                            if (typeMove == TypeMove.TypeMove.real):
                                self.sendAndMove(player, x, y, x1, y1)

                            self.board.movePiece(x, y, x1, y1)
                            self.jumpAgain=(False,None,None)
                            moved = True
                            break
                    # if it can be kinged and updates the piece to a king
                    if self.isKing(x1,y1):
                        self.board.updatePieceType(1,x1,y1)

            #check is the game is over
            self.checkWin(typeMove=TypeMove.TypeMove.real)

        return moved

    #ends the players turn
    def turnEnd(self):
        self.turn+=1

    def AI(self):
        moveFinished= False
        # if turn is AI s
        if self.getTurn() == "AI":

            # using the alpha beta function to get the best possible score
            score = self.alpha_beta(self,"AI", 0,-10000,10000,0)

            while self.getTurn() == "AI" and  not self.isOver():
                # alpha_beta function assigns best_move
                movstr = self.best_move
                if score == -10000 or len(self.getMoves("AI")) == 0:
                    # if score == -10000  or length of moves for AI is 0 then no moves for available
                    # game over then
                    self.game_over = True
                # parses movstr to move the piece
                x1 = movstr[0]
                y1 = movstr[1]
                x2 = movstr[2]
                y2 = movstr[3]
                moveFinished = self.movePiece("AI",x1, y1, x2, y2, TypeMove.TypeMove.real)
                # checks if that piece can jump again
                movs = self.canJump(x2, y2)
                # if can jump again call alpha beta again to get the next best possibe move
                # loop starts again
                if movs and not moveFinished:
                    score = self.alpha_beta(self,"AI", 0,-10000,10000, 0)
                # piece can't jump again and has moved end turn breaks the while looks
                else:
                    self.turnEnd()
        # returns a tuple for GUI to highlight the piece moved
        if moveFinished  :
            return ((x1),(y1),(x2),(y2))

    # returns if its players turn or AI's turn
    def getTurn(self):
        if(self.turn % 2 == 0):
            return "Player"
        else:
            return "AI"
    """
        checks if a piece can be Kinged when AI piece hits bottom of board
         or Player piece hits the top of the board
    """
    def isKing(self,x,y):
        self.p = Piece.Piece()
        self.p = self.board.getPieceAt(x, y)
        if(self.board.pieceAt(x, y)):
            if self.p.getOwner() == "AI" and y == self.board.getSize()-1:
                return True
            elif self.p.getOwner() == "Player" and y == 0 :
                return True
            else:
                return False
        else:
            return False
    """
        returns the moves for the piece at x y if it can jump
    """
    def canJump(self,x,y):
        moves = []
        tmp = self.board.getPieceAt(x, y)
        if tmp:
            start = 0
            finish = 0
            if tmp.getType() == 0:
                if tmp.getOwner() == "Player":
                    start = -1
                    finish = 0

                if tmp.getOwner() == "AI":
                    start = 1
                    finish = 2
                # Ai  # +1,-1 #-1 -1  player # +1 +1#-1 +1
                for i in range(-1,2):
                    for j in range (start,finish):
                        if (x +i < self.board.getSize() and x+i >=0) and (y+j <self.board.getSize() and y+j >=0):
                            tmp1 = self.board.getPieceAt(x+i, y+j)
                            if tmp1:
                                if tmp.getOwner() != tmp1.getOwner() :
                                    if self.validMove(x+i+i, y+j+j):
                                        moves.append(str(x)+","+str(y) +","+str(x+i+i)+","+str(y+j+j))

            #if piece is king then will try get all directions
            if tmp.getType() == 1:
                for i in range(-1,2):
                    for j in range (-1,2):
                        if (x +i < self.board.getSize() and x+i >=0) and (y+j <self.board.getSize() and y+j >=0):
                            tmp1 = self.board.getPieceAt(x+i, y+j)
                            if tmp1:
                                if tmp.getOwner() != tmp1.getOwner() :
                                    if self.validMove(x+i+i, y+j+j):
                                        moves.append(str(x)+","+str(y) +","+str(x+i+i)+","+str(y+j+j))

        return moves
    """
        returns the moves for the piece at x y if it can move
    """
    def pieceMovable(self,x,y):
        moves = []
        tmp = self.board.getPieceAt(x,y)
        if tmp :
            # if tmp is a king then check up left, up right, down left , down right
            if tmp.getType() == 1:
                if self.validMove(x-1, y-1):
                    moves.append(str(x-1)+","+str(y-1))

                if self.validMove(x+1, y-1):
                    moves.append(str(x+1)+","+str(y-1))

                if self.validMove(x-1, y+1):
                    moves.append(str(x-1)+","+str(y+1))

                if self.validMove(x+1, y+1):
                    moves.append(str(x+1)+","+str(y+1))
            # Players pieces which will always be at the bottom
            elif tmp.getOwner() == "Player" and tmp.getType() == 0:

                # UP and left
                if self.validMove(x-1, y-1):
                    moves.append(str(x-1)+","+str(y-1))
                # Up and right
                if self.validMove(x+1, y-1):
                    moves.append(str(x+1)+","+str(y-1))

            # AI pieces which will always be at the Top
            elif tmp.getOwner() == "AI" and tmp.getType() == 0:

                #down and right
                if self.validMove(x+1, y+1):
                        moves.append(str(x+1)+","+str(y+1))
                #down and left
                if self.validMove(x-1, y+1):
                    moves.append(str(x-1)+","+str(y+1))

        return moves

    # gets all the moves available to the player
    def getMoves(self,player):

        movableP = []
        # if it can jump again just get the moves that piece can jump again.
        if self.jumpAgain[0]:
            movableP = self.canJump(self.jumpAgain[1], self.jumpAgain[2])
        #check if any pieces can jump and just return the list of jumpable pieces and nothing else.
        else:
            movableP = self.forceJump(player)

        # if there is no pieces that can jump for the player return the movable pieces
        if not movableP:

            for i in range (self.board.getSize()):
                for j in range (self.board.getSize()):
                    tmp = self.board.getPieceAt(i,j)
                    if tmp and tmp.getOwner() == player:
                            tmpMoves =self.pieceMovable(i, j)
                            if tmpMoves:
                                for p in range (len(tmpMoves)):
                                    movableP.append(str(i)+","+str(j)+","+str(tmpMoves[p]))
        return movableP

    # evaluates the player for minimax with alpha beta pruning
    def evaluate(self, playerTurn):
        player = 0
        ai = 0
        for i in range(0, self.board.getSize()):
            for j in range(0, self.board.getSize()):
                tmp = self.board.getPieceAt(i, j)
                if tmp:
                    if tmp.getOwner() == "Player":
                        if tmp.getType() == 0:
                            player += 5
                            # Player piece at the left, top or right edge +2 as its a space position
                            if i == 0 or i == self.board.getSize() - 1 or j == 0:
                                player += 2
                        if tmp.getType() == 1:
                            player += 10
                            # stopping king moving between edge and the next empty space repeatedly
                            if i == 0 or i == self.board.getSize() - 1 or j == 0 or j == self.board.getSize() - 1:
                                player -= 10
                    if tmp.getOwner() == "AI":
                        if tmp.getType() == 0:
                            ai += 5
                            # AI if piece at the left, bottom or right edge +2 as its a space position
                            if i == 0 or i == self.board.getSize() - 1 or j == self.board.getSize() - 1:
                                ai += 2
                        if tmp.getType() == 1:
                            ai += 10
                            # stopping king moving between edge and the next empty space repeatedly
                            if i == 0 or i == self.board.getSize() - 1 or j == 0 or j == self.board.getSize() - 1:
                                ai -= 10
        # returns in favour of the playersTurn for minimax
        if playerTurn == "AI":
            return player - ai
        else:
            return ai - player

    """
        minimax with alpha beta pruning
    """

    def alpha_beta(self, board, player, ply, alpha, beta, recursive):

        # rabbit = RabbitClient()
        # result = "fuck"
        #
        # if (recursive == 0):
        #     result = rabbit.call("")
        #     # s = socket.socket()
        #     # s.connect(('188.166.85.167', 8080))
        #     # print("sended")
        #     # s.send(("").encode())

        QCoreApplication.processEvents()
        # amount of moves to look ahead currently 3 moves ahead

        ply_depth = 1
        # check for end state.
        board.checkWin(typeMove=TypeMove.TypeMove.im)
        if ply >= ply_depth or board.isOver():
            # return evaluation of board  if we reached final ply or end state
            score = board.evaluate(player)
            # if (recursive == 0):
            #     print("result")
            #     print(result)
            #     # print("123")
            #     # receive = s.recv(1024)
            #     # print("Client received: " + str(receive))
            #     # s.close()
            return score
        # gets moves for the player.
        moves = board.getMoves(player)
        # Max's Turn
        if player == "AI" and not ply == ply_depth:  # if AI to play on node
            # ply%2 is 0 every second turn
            # For each child of the root node.
            for i in moves:
                # create a deep copy of the board "Assignment statements in Python do not copy objects"
                # or else it is just a reference
                new_board = deepcopy(board)
                # parsing the value of i, moves
                x1 = int(i[0])
                y1 = int(i[2])
                x2 = int(i[4])
                y2 = int(i[6])
                # moving the piece
                finishMove = new_board.movePiece("AI", x1, y1, x2, y2, TypeMove.TypeMove.im)
                if finishMove:
                    # if move is true then next player and ply +1
                    if player == 'AI':
                        player = 'Player'
                    # score = alpha-beta(next players turn,child,alpha,beta)
                    score = self.alpha_beta(new_board, player, ply + 1, alpha, beta, 1)
                else:
                    # else its still that players turn possibly more then one jump can happen.
                    player = "AI"
                    score = self.alpha_beta(new_board, player, ply, alpha, beta, 1)

                # if score > alpha then alpha = score found a better move
                if score > alpha:
                    if ply == 0:
                        self.best_move = (x1, y1, x2, y2)  # save the move best move
                    # assign the better score to alpha
                    alpha = score
                # if alpha >= beta then return alpha (cut off)
                if alpha >= beta:
                    # if (recursive == 0):
                    #     print("result")
                    #     print(result)
                    #     # print("123")
                    #     # receive = s.recv(1024)
                    # print("Client received: " + str(receive))
                    # s.close()
                    return alpha
                    # return alpha this is our best score
                    # if (recursive == 0):
                    #     print("result")
                    #     print(result)
                    #     # print("123")
                    #     # receive = s.recv(1024)
                    #     # print("Client received: " + str(receive))
                    # s.close()
            return alpha

        # Mins turn
        elif player == "Player" and not ply == ply_depth:  # the opponent of the AI to play on this node
            # ply%2 is 1 every second turn
            # For each child
            for i in moves:
                # create a deep copy of the board "Assignment statements in Python do not copy objects"
                # or else it is just a reference
                new_board = deepcopy(board)
                # parsing the value of i, moves
                x1 = int(i[0])
                y1 = int(i[2])
                x2 = int(i[4])
                y2 = int(i[6])
                # moving the piece
                finishMove = new_board.movePiece("Player", x1, y1, x2, y2, TypeMove.im)
                if finishMove:
                    # if move is true then next player and ply +1
                    if player == 'Player':
                        player = 'AI'
                    # score = alpha-beta(next players turn,child,alpha,beta)
                    score = self.alpha_beta(new_board, player, ply + 1, alpha, beta, 1)
                else:
                    # else its still that players turn possibly more then one jump can happen.
                    player = 'Player'
                    score = self.alpha_beta(new_board, player, ply, alpha, beta, 1)

                # if score < beta then beta = score, opponent found a better, worse move
                if score < beta:
                    beta = score
                # if alpha >= beta then return beta (cut off)
                if alpha >= beta:
                    # if (recursive == 0):
                    #     print("result")
                    #     print(result)
                    #     # print("123")
                    # receive = s.recv(1024)
                    # print("Client received: " + str(receive))
                    # s.close()
                    return beta
                    # return beta the opponent's best move

                    # if (recursive == 0):
                    #     print("result")
                    #     print(result)
                    #     # print("123")
                    # receive = s.recv(1024)
                    # print("Client received: " + str(receive))
                    # s.close()

            return beta

        # sock = socket.socket()
        # sock.bind(('', 9090))
        #
        # sock.listen(1)
        # conn, addr = sock.accept()
        #
        # data = conn.recv(1024)
        #
        # print("Server received: " + data)
        #
        # conn.send(("").encode())
        #
        # conn.close()
        #
        #
        # QCoreApplication.processEvents()
        # # amount of moves to look ahead currently 3 moves ahead
        # return beta

