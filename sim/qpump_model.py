"""Integer reference model of Qpump.h economics, used to fuzz the money invariants.

It mirrors the contract formulas one to one: CurveCost, TradeFee, the opening batch,
exact-token buys, sells, graduation budget and refunds.
"""
import random

N = 710_000_000
RESERVE = 290_000_000
LIN, SLOPE, DEN = 1_420_000_000_000, 9000, 1_420_000_000_000
OPEN_TOKEN_CAP, OPEN_QU_CAP = 177_500_000, 377_187_500
LAUNCH_FEE, REWARD, GRAD_BURN, MIN_FEE = 25_000_000, 50_000_000, 10_000_000, 1000
QX_ISSUE, QX_XFER, POOL_FEE, LIQ_FEE = 1_000_000_000, 100, 200_000_000, 100_000


def curve_cost(a, b, up):
    if a < 0 or b <= a or b > N:
        return 0
    num = LIN * (b - a) + SLOPE * (b * b - a * a)
    q = num // DEN
    return q + 1 if up and q * DEN < num else q


def trade_fee(amount, inclusive):
    if amount <= 0:
        return MIN_FEE
    den = 10100 if inclusive else 10000
    num = amount * 100
    q = num // den + (1 if (num // den) * den < num else 0)
    return max(q, MIN_FEE)


def tokens_for_qu(frm, budget, limit):
    lo, hi = 0, min(limit, N - frm)
    if hi <= 0 or budget <= 0:
        return 0
    while lo < hi:
        mid = lo + ((hi - lo + 1) >> 1)
        if curve_cost(frm, frm + mid, True) <= budget:
            lo = mid
        else:
            hi = mid - 1
    return lo


class Coin:
    def __init__(self):
        self.real_qu = 0
        self.sold = 0
        self.batch_qu = 0
        self.batch_tokens = 0
        self.settled = False
        self.holders = {}   # id -> [tokens, openingQu]
        self.pots = 0       # fees collected (shareholders + burn), for balance accounting
        self.batch_participants = set()

    def eff(self, e):
        t = e[0]
        if e[1] > 0 and self.settled and self.batch_qu > 0:
            t += self.batch_tokens * e[1] // self.batch_qu
        return t

    def opening_order(self, who, amount):
        if amount <= 0 or OPEN_QU_CAP - self.batch_qu <= 0:
            return 0
        avail = amount
        fee = trade_fee(avail, True)
        net = avail - fee
        room = OPEN_QU_CAP - self.batch_qu
        if net > room:
            net = room
            fee = trade_fee(net, False)
        used = net + fee
        if used > amount:
            net -= used - amount
            used = amount
        if net <= 0:
            return 0
        self.holders.setdefault(who, [0, 0])[1] += net
        self.batch_participants.add(who)
        self.batch_qu += net
        self.pots += fee
        assert used <= amount
        return used

    def settle(self):
        self.batch_tokens = tokens_for_qu(0, self.batch_qu, OPEN_TOKEN_CAP) if self.batch_qu > 0 else 0
        self.real_qu = self.batch_qu
        self.sold = self.batch_tokens
        self.settled = True

    def buy(self, who, tokens, reward):
        if tokens <= 0:
            return 0
        tokens = min(tokens, N - self.sold)
        if tokens <= 0:
            return 0
        e = self.holders.get(who, [0, 0])
        e = [self.eff(e), 0]
        cost = curve_cost(self.sold, self.sold + tokens, True)
        fee = trade_fee(cost, False)
        total = cost + fee
        if total > reward:
            return 0
        e[0] += tokens
        self.holders[who] = e
        self.real_qu += cost
        self.sold += tokens
        self.pots += fee
        return total

    def sell(self, who, tokens):
        if who not in self.holders or tokens <= 0:
            return 0
        e = [self.eff(self.holders[who]), 0]
        if tokens > e[0] or tokens > self.sold:
            return 0
        gross = curve_cost(self.sold - tokens, self.sold, False)
        fee = trade_fee(gross, False)
        assert gross <= self.real_qu, ("sell would exceed reserve", gross, self.real_qu)
        if gross <= fee:
            return 0
        e[0] -= tokens
        if e[0] == 0:
            del self.holders[who]
        else:
            self.holders[who] = e
        self.real_qu -= gross
        self.sold -= tokens
        self.pots += fee
        return gross - fee

    def transfer(self, frm, to, tokens):
        if frm not in self.holders or frm == to or tokens <= 0:
            return False
        e = [self.eff(self.holders[frm]), 0]
        if tokens > e[0]:
            return False
        t = self.holders.get(to, [0, 0])
        t = [self.eff(t), 0]
        t[0] += tokens
        self.holders[to] = t
        e[0] -= tokens
        if e[0] == 0:
            del self.holders[frm]
        else:
            self.holders[frm] = e
        return True

    def check(self):
        held = sum(self.eff(e) for e in self.holders.values())
        assert held <= self.sold, ("holders exceed sold", held, self.sold)
        assert self.sold - held <= len(self.batch_participants), ("dust too large", self.sold - held)
        assert self.real_qu >= curve_cost(0, self.sold, False), ("reserve below curve area", self.real_qu)

    def graduation(self):
        deliver = len(self.holders) * QX_XFER * 2
        pool_qu = self.real_qu - (QX_ISSUE + REWARD + GRAD_BURN + POOL_FEE + LIQ_FEE + deliver)
        pool_tokens = min(pool_qu * 1000 // 10000, RESERVE)
        assert pool_qu > 0 and 0 < pool_tokens <= RESERVE
        price = pool_qu / pool_tokens
        assert 10 <= price < 10.0001, price
        return pool_qu, pool_tokens, deliver

    def refunds(self):
        snap_qu, snap_sold = self.real_qu, self.sold
        paid = 0
        out = {}
        for who, e in self.holders.items():
            q = snap_qu * self.eff(e) // snap_sold if snap_sold > 0 else 0
            q = min(q, snap_qu - paid)
            paid += q
            out[who] = q
        assert paid <= snap_qu
        return paid, snap_qu, out


def run(seed):
    rng = random.Random(seed)
    c = Coin()
    ids = list(range(rng.randint(2, 60)))
    for _ in range(rng.randint(0, 80)):
        c.opening_order(rng.choice(ids), rng.choice([1, 999, 5_000, 5_000_000, 25_000_000, 100_000_000, 400_000_000]))
    c.settle()
    c.check()
    for _ in range(rng.randint(10, 400)):
        who = rng.choice(ids)
        if rng.random() < 0.6:
            t = rng.choice([1_000_000, 10_000_000, 50_000_000, 150_000_000])
            c.buy(who, t, 10**13)
        elif who in c.holders and rng.random() < 0.7:
            e = c.eff(c.holders[who])
            if e > 0:
                c.sell(who, rng.randint(1, e))
        elif who in c.holders:
            e = c.eff(c.holders[who])
            if e > 0:
                c.transfer(who, rng.choice(ids), rng.randint(1, e))
        c.check()
    paid, snap, out = c.refunds()
    # force completion and graduation budget check
    whale = 10**6
    c.buy(whale, N - c.sold, 10**14)
    c.check()
    g = c.graduation() if c.sold == N else None
    # everyone sells back from a full curve without breaking the reserve
    for who in list(c.holders):
        e = c.eff(c.holders[who])
        if e > 0:
            c.sell(who, e)
    c.check()
    return g


if __name__ == "__main__":
    for seed in range(3000):
        run(seed)
    print("3000 randomized runs passed")
    c = Coin(); c.settle(); c.buy(1, N, 10**14)
    print("full-curve graduation budget:", c.graduation(), "raise", c.real_qu)
