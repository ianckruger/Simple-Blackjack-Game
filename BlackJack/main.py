import random as rand
import os
import time
from database_utils import init_db, renderHand, recordRound, getPlayerStats

suits = ["H", "D", "S", "C"]
ranks = ["2","3","4", "5", "6", "7", "8", "9", "10","J","Q","K","A"]
deck = [rank + suit for suit in suits for rank in ranks]
values ={
    "2": 2, "3": 3, "4": 4, "5": 5, "6": 6,
    "7": 7, "8": 8, "9": 9, "10": 10,
    "J": 10, "Q": 10, "K": 10
}

def shuffleCards() :
    # While Original array is not empty, add to new array
    newCards = []
    while len(deck) != len(newCards):
        index = rand.randint(0,len(deck)-1)
        newCards.append(deck[index])

    return newCards

def getCard(playedCards,cards, totalValue, dealer=False):
    index = rand.randint(0,len(cards)-1)
    card1 = cards[index]
    playedCards.append(card1)
    cards.pop(index)

    if not dealer:
        if (card1[:-1] == "A"):
            if totalValue > 10:
                totalValue += 1
            else:
                choice = input("Would you like to count Ace as 1 or 11?: ")
                if str(choice) == "11":
                    totalValue += 11
                else:
                    totalValue += 1
        else:
            totalValue += values[card1[:-1]]

        return totalValue
    else:
        if (card1[:-1] == "A"):
            if totalValue > 10:
                totalValue += 1
            else:
                totalValue += 11
        else:
            totalValue += values[card1[:-1]]

        return totalValue


def compareCards(playerCards, dealerCards, totalValue, dealerValue, playingDeck):
    # Print out cards in playedCards and also dealer cards. 
    printTable(playerCards, dealerCards, hideFirst=False)
    while(dealerValue < 17):
        dealerValue = getCard(dealerCards, playingDeck, dealerValue, dealer=True)
        printTable(playerCards, dealerCards, False)
    
    # Dealer has 17 or over, break and compare
    if ( dealerValue > totalValue and dealerValue < 22):
        print("You lose. Better luck next time!")
        return "lose"
    elif dealerValue == totalValue:
        print("Push. Next game")
        return "push"
    
    else:
        print("You win! Congradulations")
        return "win"


def printTable(playerCards, dealerCards, hideFirst=True):
    os.system('cls')
    print(renderHand(dealerCards, hideFirst))
    print(renderHand(playerCards))

def playRound(outcome):
    totalValue = 0
    dealerValue = 0
    playingDeck = shuffleCards()
    playerCards = []
    dealerCards= []
    dealerValue = getCard(dealerCards, playingDeck, dealerValue, dealer=True)
    dealerValue = getCard(dealerCards, playingDeck, dealerValue, dealer=True)
    endRound = False
    while(not endRound):
        totalValue = getCard(playerCards, playingDeck, totalValue)
        printTable(playerCards, dealerCards)
        print(totalValue)
        if(totalValue == 21):
            print("Blackjack! You win.")
            endRound = True
            return "blackjack"
            
        elif(totalValue > 21):
            print("You lose.")
            endRound = True
            return "lose"
            break
        if(len(playerCards) >= 2):
            choice = input("Would you like to hit or hold?")
            if choice == "hit":
                pass
            else:
                outcome = compareCards(playerCards, dealerCards, totalValue, dealerValue, playingDeck)
                return outcome

    
    


    # if  not overLimit:
    #     card3 = getCard(playedCards, playingDeck)
    #     displayCards()

def login(username):
    print("Do you want to login (or not, and continue as guest)?")
    choice = input("Y/N: ")
    saveStats = False
    if (choice.lower() == "y"):
        saveStats = True
        username += input("Username: ")

    return saveStats



if __name__ == "__main__":
    init_db()
    username = ""
    outcome = ""
    saveStats = login(username)
    play = True
    while play:
        outcome = playRound(outcome)
        if saveStats:
            recordRound(username, outcome)
        choice = input("Would you like to play again? Y/N: ")
        if choice.lower() != "y":
            play = False

