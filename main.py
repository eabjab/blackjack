# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

import random

fullDeck = ["2", "2", "2", "2", "3", "3", "3", "3", "4", "4", "4", "4", "5", "5", "5", "5", "6", "6", "6", "6", "7",
            "7", "7", "7", "8", "8", "8", "8", "9", "9", "9", "9", "10", "10", "10", "10", "J", "J", "J", "J", "Q", "Q",
            "Q", "Q", "K", "K", "K", "K", "A", "A", "A", "A"]

scoreTable = {
    "2": 2,
    "3": 3,
    "4": 4,
    "5": 5,
    "6": 6,
    "7": 7,
    "8": 8,
    "9": 9,
    "10": 10,
    "J": 10,
    "Q": 10,
    "K": 10,
    "A": 1,
}


def scoreHand(hand):
    score = 0
    has_ace = False

    for card in hand:
        score += scoreTable[card]

        if card == "A":
            has_ace = True

    if has_ace and score <= 11:
        score += 10

    return score


def countCards(cardList):
    # reset count dict
    card_counts = {
        "2": 0,
        "3": 0,
        "4": 0,
        "5": 0,
        "6": 0,
        "7": 0,
        "8": 0,
        "9": 0,
        "10": 0,
        "J": 0,
        "Q": 0,
        "K": 0,
        "A": 0,
    }

    for card in cardList:
        card_counts[card] += 1

    return card_counts


def getCardProb(card_counts):
    card_probabilities = card_counts.copy()
    total = sum(card_counts.values())
    for card in card_counts:
        card_probabilities[card] /= total

    return card_probabilities


# TODO ideas to go faster
# reduce branching factor
# multi processing
# cache results
# simulate results
# maybe pass running probability up thru recursion to determine when to simulate instead of calculate

# TODO expected values for blackjack/double down/split cases
# initial call should be recursivePlay([], [], card_count, False) as of now
def getWinProbability(p_hand, d_hand, card_count, p_turn):
    p_score = scoreHand(p_hand)
    d_score = scoreHand(d_hand)

    if p_score > 21:  # player busts
        return 0
    if d_score > 21:  # dealer busts
        return 1
    # TODO implement something to determine if hand is a split hand and therefore not blackjack
    if (len(p_hand) == 2) and (p_score == 21):  # player blackjack
        return 1
    if (len(d_hand) == 2) and (len(p_hand) == 2) and (d_score == 21):  # dealer blackjack
        return 0
    if (not p_turn) and (d_score >= 17):  # neither busts, so we compare hands
        if p_score > d_score:  # player wins
            return 1
        elif p_score < d_score:  # dealer wins
            return 0
        else:  # push
            return 0

    # summation of player win probabilities for each card drawn (return value)
    total_prob = 0
    card_prob = getCardProb(card_count)
    for card in card_count:
        if card_count[card] <= 0:
            continue
        # get probability of card being dealt
        prob = card_prob[card]
        # create copies to pass down recursion
        p_copy = p_hand[:]
        d_copy = d_hand[:]
        card_copy = card_count.copy()

        if p_turn:  # player's turn
            # TODO combine logic
            if (len(p_copy) == 0) and (len(d_copy) == 1):  # deal player's first card (recursion 1)
                p_copy.append(card)
                card_copy[card] -= 1
                # probability of drawing this card * probability of winning
                prob *= getWinProbability(p_copy, d_copy, card_copy, False)
            elif (len(p_copy) == 1) and (len(d_copy) == 2):  # deal player's second card (recursion 3)
                p_copy.append(card)
                card_copy[card] -= 1
                prob *= getWinProbability(p_copy, d_copy, card_copy, True)
            elif len(d_copy) == 2:  # player's turn to make a decision

                # stand and make it dealer's turn
                stand_prob = getWinProbability(p_copy, d_copy, card_copy, False)

                hit_prob = 0
                if p_score < 21:  # hit and keep it player's turn
                    p_copy.append(card)
                    card_copy[card] -= 1
                    hit_prob = getWinProbability(p_copy, d_copy, card_copy, True)

                # probability of winning from current position with optimal decisions
                optimal_prob = max(stand_prob, hit_prob)

                # probability of drawing most recent card * probability of winning with optimal decisions
                prob *= optimal_prob

                # TODO double down decision tree
                # TODO split decision tree

        else:  # dealer's turn
            # TODO combine logic
            if (len(p_copy) == 0) and (len(d_copy) == 0):  # deal first card to dealer (recursion 0)
                d_copy.append(card)
                card_copy[card] -= 1
                prob *= getWinProbability(p_copy, d_copy, card_copy, True)
            elif (len(p_copy) == 1) and (len(d_copy) == 1):  # deal dealer's second card (recursion 2)
                d_copy.append(card)
                card_copy[card] -= 1
                prob *= getWinProbability(p_copy, d_copy, card_copy, True)
            else:
                if d_score < 17:  # dealer must keep hitting until 17
                    d_copy.append(card)
                    card_copy[card] -= 1
                    prob *= getWinProbability(p_copy, d_copy, card_copy, False)

        total_prob += prob

    return total_prob


class Shoe:
    def __init__(self, numDecks):
        self.card_list = []
        for i in range(numDecks):
            self.card_list += fullDeck

        self.card_counts = countCards(self.card_list)
        self.card_probabilities = getCardProb(self.card_counts)

    def shuffle(self):
        random.shuffle(self.card_list)

    def draw(self):
        card = self.card_list.pop()
        self.card_counts[card] -= 1
        return card

    # TODO either remove or find alternative because this is garbage
    def faceDown(self):
        return self.card_list.pop()

    def faceUp(self, card):
        self.card_counts[card] -= 1


class Dealer:

    def __init__(self):
        self.show_card = "-1"
        self.hidden_card = "-1"
        self.hand = []
        self.score = 0
        self.canHit = True

    def drawShow(self, shoe):
        card = shoe.draw()
        self.show_card = card
        self.hand.append(card)
        self.setScore()

    def drawHidden(self, shoe):
        card = shoe.faceDown()
        self.hidden_card = card
        self.hand.append(card)
        self.setScore()

    def hit(self, shoe):
        self.hand.append(shoe.draw())
        self.setScore()

    def setScore(self):
        self.score = scoreHand(self.hand)

    def playHand(self, shoe):
        while self.score < 17:
            self.hit(shoe)

    def offerInsurance(self):
        return (len(self.hand) == 2) and self.hand[0] == "A"

    def hasBlackjack(self):
        return (len(self.hand) == 2) and (self.score == 21)


class Player:

    def __init__(self, pid):
        self.id = pid
        self.hand = []
        self.score = 0
        self.bet = 0
        self.split_hand = []
        self.split_score = 0
        self.split_bet = 0
        self.can_hit = True

    def setScore(self):
        self.score = scoreHand(self.hand)
        self.split_score = scoreHand(self.split_hand)

    def hit(self, shoe):
        self.hand.append(shoe.draw())
        self.setScore()

    def doubleDown(self, shoe):
        self.hand.append(shoe.draw())
        self.bet = self.bet * 2
        self.can_hit = False
        self.setScore()

    # TODO fix splitting, it *might* be a mess
    def split(self):
        self.split_hand.append(self.hand.pop())
        self.split_bet = self.bet
        self.setScore()

    def hasBlackjack(self):
        return (len(self.split_hand) == 0) and (len(self.hand) == 2) and (self.score == 21)


class Game:

    def __init__(self, numPlayers, numDecks):
        self.shoe = Shoe(numDecks)
        self.shoe.shuffle()
        self.dealer = Dealer()
        self.players = list()

        for n in range(numPlayers):
            self.players.append(Player(n))

    def deal(self):
        # deal first card to all players
        for player in self.players:
            player.hit(self.shoe)
        # give face up card to dealer
        self.dealer.drawShow(self.shoe)
        # deal second card to all players
        for player in self.players:
            player.hit(self.shoe)
        # give dealer face down card
        self.dealer.drawHidden(self.shoe)

    def showHands(self):
        print("Dealer: " + ", ".join(self.dealer.hand))
        print("Score: " + str(self.dealer.score))

        for player in self.players:
            print("Player " + str(player.id) + ": " + ", ".join(player.hand))
            print("Score: " + str(player.score))


if __name__ == '__main__':
    s1 = Shoe(1)
    player_hand = []
    dealer_hand = []

    win_prob = getWinProbability(player_hand, dealer_hand, s1.card_counts, False)
    print(win_prob)
    print(player_hand)
    print(dealer_hand)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
