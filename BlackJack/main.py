import random as rand

cards = [2,3,4,5,6,7,8,9,10,"J","Q","K","A",2,3,4,5,6,7,8,9,10,"J","Q","K","A",2,3,4,5,6,7,8,9,10,"J","Q","K","A",2,3,4,5,6,7,8,9,10,"J","Q","K","A"]

def shuffleCards(cardArray) :
    # While Original array is not empty, add to new array
    newCards = []
    while cardArray:
        index = rand.randint(1,len(cardArray))
        newCards.append(cardArray[index])

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
    shuffleCards(cards)
    playedCards = []
    card1 = getCard(playedCards, cards)
    card2 = getCard(playedCards, cards)
    overLimit = displayCards()
    if  not overLimit:
        card3 = getCard(playedCards, cards)
        displayCards()


def main() {

}