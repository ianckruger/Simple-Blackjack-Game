import random as rand
from database_utils import init_db, renderHand, recordRound, getPlayerStats

suits = ["H", "D", "S", "C"]
ranks = ["2","3","4", "5", "6", "7", "8", "9", "10","J","Q","K","A"]
deck = [rank + suit for suit in suits for rank in ranks]

def shuffleCards() :
    # While Original array is not empty, add to new array
    newCards = []
    while deck:
        index = rand.randint(1,len(deck))
        newCards.append(deck[index])

    return newCards

def getCard(playedCards,cards):
    index = rand.randint(0,len(cards) -1)
    card1 = cards[index]
    playedCards.append(card1)
    cards.pop(index)

    return card1

def displayCards():
    # Print out cards in playedCards, if total card points over 21, or == 21, return 

    return False

def compareCards():

    return True

def playRound():
    deck = shuffleCards()
    playedCards = []
    card1 = getCard(playedCards, cards)
    card2 = getCard(playedCards, cards)
    overLimit = displayCards()
    if  not overLimit:
        card3 = getCard(playedCards, cards)
        displayCards()

def login():
    print("Do you want to login (or not, and continue as guest)?")
    choice = input("Y/N")
    saveStats = False
    if (choice.lower == "y"):
        saveStats = True
        username = input("Username: ")



if __name__ == "__main__":
    # init_db()                         # create DB & defaults on first run
    # # set_active_theme("ascii")       # try the ASCII look
    # print(renderHand([("A","S"), ("10","H")]))
    # print()
    # print(renderHand([("K","D"), ("7","C"), ("3","H")], hideFirst=True))

    # # Record a couple of sample rounds
    # recordRound("player1", bet=10, outcome="win", delta=+10, playerTotal=21, dealerTotal=18)
    # recordRound("player1", bet=10, outcome="blackjack", delta=+15, playerTotal=21, dealerTotal=20)
    # recordRound("player1", bet=10, outcome="lose", delta=-10, playerTotal=18, dealerTotal=19)
    # print("\nStats:", getPlayerStats("player1"))
    init_db()
    login()
    playRound()
    print(getPlayerStats("player1"))  