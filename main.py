import random

# deprecated -- use deck_values instead to reduce branching factor of recursive probability calculations
fullDeck = ["2", "2", "2", "2", "3", "3", "3", "3", "4", "4", "4", "4", "5", "5", "5", "5", "6", "6", "6", "6", "7",
            "7", "7", "7", "8", "8", "8", "8", "9", "9", "9", "9", "10", "10", "10", "10", "J", "J", "J", "J", "Q", "Q",
            "Q", "Q", "K", "K", "K", "K", "A", "A", "A", "A"]

deck_values = [1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 6, 6, 6, 6, 7, 7, 7, 7, 8, 8, 8, 8, 9, 9, 9,
               9, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10]


def countCards(card_list):
    card_count = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0, 10: 0}
    for card in card_list:
        card_count[card] += 1

    return card_count


def scoreHand(hand):
    score = 0
    has_ace = False

    for card in hand:
        score += card
        if card == 1:
            has_ace = True

    if has_ace and score <= 11:
        score += 10

    return score


def getCardProb(card_counts):
    card_probabilities = card_counts.copy()
    total = sum(card_counts.values())
    for card in card_counts:
        card_probabilities[card] /= total

    return card_probabilities


def getCardTuple(card_counts):
    return tuple(card_counts.values())


# d_hand should be a list with length 1 containing only dealer's face up card
# using expected values instead of probability for now but switching is easy
# TODO double check split calculation because values seem a bit high
def getDecision(p_hand, d_hand, card_count, cached_hands, p_turn, split):
    p_score = scoreHand(p_hand)
    d_score = scoreHand(d_hand)
    p_hand_size = len(p_hand)
    d_hand_size = len(d_hand)

    if p_score > 21:  # player busts
        return [-1] * 4
    if d_score > 21:  # dealer busts
        return [1] * 4
    if (p_score == 21) and (p_hand_size == 2) and not split:  # player blackjack
        return [1.5] * 4
    if (d_score == 21) and (d_hand_size == 2):  # dealer blackjack
        return [-1] * 4
    if (not p_turn) and (d_score >= 17):  # neither busts, so we compare hands
        if p_score > d_score:  # player wins
            return [1] * 4
        elif p_score < d_score:  # dealer wins
            return [-1] * 4
        else:  # push
            return [0] * 4

    total_expected_values = [0] * 4
    card_prob = getCardProb(card_count)

    card_tuple = getCardTuple(card_count)
    # if we have already calculated expected value for a permutation of the current hand, don't recalculate it
    if card_tuple in cached_hands:
        return cached_hands[card_tuple]

    for card in card_count:
        if card_count[card] <= 0:
            continue
        # get probability of card being dealt
        prob = card_prob[card]

        expected_values = [0] * 4  # will always be overridden
        if p_turn:
            # stand
            stand_expected_value = -1 * prob
            # if player has 0% chance to bust, don't even consider standing
            if p_score > 11:
                stand_expected_value = prob * max(getDecision(p_hand, d_hand, card_count, dict(), False, split))
                # if split and first card is ace

            # hit
            hit_expected_value = -1 * prob
            double_ev = -2 * prob
            if p_score < 21:
                card_copy = card_count.copy()
                p_copy = p_hand[:]

                p_copy.append(card)
                card_copy[card] -= 1
                hit_expected_value = prob * max(getDecision(p_copy, d_hand, card_copy, cached_hands, True, split))
                # double down
                if p_hand_size == 2 and not split:
                    double_ev = 2 * prob * max(getDecision(p_copy, d_hand, card_copy, dict(), False, split))

            # split
            split_ev = -2 * prob
            if not split and p_hand_size == 2 and p_hand[0] == p_hand[1]:
                split_ev = 0
                card_copy = card_count.copy()
                p_left = p_hand[:1]
                p_right = p_hand[1:]
                left_cache = dict()
                right_cache = dict()

                aces = (p_left[0] == 1) and (p_right[0] == 1)

                p_left.append(card)
                card_copy[card] -= 1
                split_card_prob = getCardProb(card_copy)
                # first two cards after split are dealt immediately so take all combinations into account
                for right_card in card_copy:
                    if card_copy[right_card] <= 0:
                        continue

                    split_prob = split_card_prob[right_card]

                    split_copy = card_count.copy()
                    p_right_copy = p_right[:]

                    split_copy[right_card] -= 1
                    p_right_copy.append(right_card)

                    # if split aces, clear cache for dealers turn
                    if aces:
                        left_cache = dict()
                        right_cache = dict()

                    left_ev = prob * split_prob * max(
                        getDecision(p_left, d_hand, split_copy, left_cache, not aces, True))
                    right_ev = prob * split_prob * max(
                        getDecision(p_right, d_hand, split_copy, right_cache, not aces, True))
                    split_ev += (left_ev + right_ev)

            expected_values = list([stand_expected_value, hit_expected_value, double_ev, split_ev])

        else:
            d_copy = d_hand[:]
            card_copy = card_count.copy()
            if d_hand_size == 1:  # check all possible dealer face down cards
                d_copy.append(card)
                card_copy[card] -= 1
                expected_values = [val * prob for val in getDecision(p_hand, d_copy, card_copy, dict(), True, split)]
            elif d_score < 17:
                d_copy.append(card)
                card_copy[card] -= 1
                expected_values = [val * prob for val in
                                   getDecision(p_hand, d_copy, card_copy, cached_hands, False, split)]

        total_expected_values = [a + b for a, b in zip(total_expected_values, expected_values)]

    cached_hands[card_tuple] = total_expected_values
    return total_expected_values


# TODO ideas to go faster
# multi processing
# simulate results

# TODO expected values for blackjack/double down/split cases
# initial call should be getWinProbability([], [], card_count, False) as of now
def getWinProbability(p_hand, d_hand, card_count, p_turn):
    p_score = scoreHand(p_hand)
    d_score = scoreHand(d_hand)

    if p_score > 21:  # player busts
        return 0
    if d_score > 21:  # dealer busts
        return 1
    # TODO implement something to determine if hand is a split hand and therefore not blackjack
    if (p_score == 21) and (len(p_hand) == 2):  # player blackjack
        return 1
    if (d_score == 21) and (len(d_hand) == 2) and (len(p_hand) == 2):  # dealer blackjack
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
            self.card_list += deck_values

        self.card_counts = countCards(self.card_list)
        self.card_probabilities = getCardProb(self.card_counts)

    def shuffle(self):
        random.shuffle(self.card_list)

    def draw(self):
        card = self.card_list.pop()
        self.card_counts[card] -= 1
        return card

    def drawCard(self, card):
        self.card_list.remove(card)
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
    s1 = Shoe(6)
    s1.shuffle()
    dealer_hand = [s1.drawCard(6)]
    player_hand = [s1.drawCard(9), s1.drawCard(9)]
    cards = s1.card_counts
    print(cards)

    print(dealer_hand)
    print(player_hand)

    decision_vector = getDecision(player_hand, dealer_hand, cards, dict(), False, False)
    print(decision_vector)
