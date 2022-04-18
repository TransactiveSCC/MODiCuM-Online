import hopcroftkarp
import sys
# Resource allocation algorithm
# subject to constraints
# sell      buy
# start <   start
# end   >   end
# cpu   >   cpu*rate
# price <   price

# sell_start < buy_start < buy_end < sell_end => (allocation_start, allocation_end)
# maximizing number of trades


def matchable(buy_offer, sell_offer, debug=True):
    match = False
    mediator = []

    if sell_offer.start > buy_offer.start:
        if debug:
            print(f"Resource not available at start")
        return match, mediator

    if sell_offer.end < buy_offer.end:
        if debug:
            print(f"Resource not available until end")
        return match, mediator

    if sell_offer.price > buy_offer.price:
        if debug:
            print(f"Price mismatch: {sell_offer.price} > {buy_offer.price}")
        return match, mediator

    if sell_offer.cpu < buy_offer.cpu * buy_offer.rate:
        # cycles/s   # cycles/request * requests/s
        if debug:
            print("Load too high")
        return match, mediator

    common_mediators = set(sell_offer.mediators).intersection(buy_offer.mediators)
    if not common_mediators:
        if debug:
            print("No commonly trusted Mediator")
        return match, mediator
    else:
        # print("Matchable")
        match = True
        return match, common_mediators


def construct_graph(buy_offers, sell_offers, mediator_offers=[]):
    #TODO: include mediator offers when constructing feasibility graph
    graph = {}
    for i in buy_offers:
        graph[i] = set()
        edges = []

        for j in sell_offers:
            [result, mediators] = matchable(buy_offers[i], sell_offers[j])
            if result:
                graph[i].add(j)
    return graph

def double_auction(buy_offers, sell_offers, allocation):

    matched_buyers = {}
    matched_sellers = {}
    for match in allocation:
        buyer = match
        buyer_price = buy_offers[buyer].price
        seller = allocation[match]
        seller_price = sell_offers[seller].price

        matched_buyers[buyer] = buyer_price
        matched_sellers[seller] = seller_price

    buying = sorted(matched_buyers.items(), key=lambda s: -s[1])
    selling = sorted(matched_sellers.items(), key=lambda s: s[1])
    print(f"buying: {buying}")
    print(f"selling: {selling}")

    bp = buying[0][1]
    sp = selling[0][1]
    bi = 0
    si = 0

    while bp > sp:
        sp = selling[si][1]
        bp = buying[bi][1]

        if buying[bi+1][1] < selling[si+1][1]:
            break

        bi += 1
        si += 1

    p = (bp + sp)/2
    # p = sp

    return {
        'buyers': buying[0:bi+1],
        'sellers': selling[0:si+1],
        'price': p
    }

def construct_final_allocation(auction_result, buy_offers, sell_offers):
    #TODO: extend to allow one buying offer to be satisfied by a set of sell offers
    allocation_final = {}
    for ix, offer in enumerate(auction_result["buyers"]):
        buy_offer_uuid = auction_result["buyers"][ix][0]
        buy_offer = buy_offers[buy_offer_uuid]
        sell_offer_uuid = auction_result["sellers"][ix][0]
        sell_offer = sell_offers[sell_offer_uuid]
        common_mediators = set(sell_offer.mediators).intersection(buy_offer.mediators)
        allocation_final[buy_offer_uuid] = {"sell_offer": sell_offer_uuid,
                                            "mediator": common_mediators.pop(),
                                            "price": auction_result["price"],
                                            "start": buy_offer.start,
                                            "end": buy_offer.end}
    return allocation_final

def construct_allocation(allocation, buy_offers, sell_offers):
    #TODO: merge construct_final_allocation and construct_allocation.
    # auction_result format is not compatible with allocation format
    allocation_final = {}
    for buy_offer_uuid in allocation:
        buy_offer = buy_offers[buy_offer_uuid]
        sell_offer_uuid = allocation[buy_offer_uuid]
        sell_offer = sell_offers[sell_offer_uuid]
        common_mediators = set(sell_offer.mediators).intersection(buy_offer.mediators)
        price = (buy_offer.price + sell_offer.price) * .5
        allocation_final[buy_offer_uuid] = {"sell_offer": sell_offer_uuid,
                                            "mediator": common_mediators.pop(),
                                            "price": price,
                                            "start": buy_offer.start,
                                            "end": buy_offer.end}
    return allocation_final


def allocate(buy_offers, sell_offers, test=False):
    graph = construct_graph(buy_offers, sell_offers)
    allocation = hopcroftkarp.HopcroftKarp(graph).maximum_matching(keys_only=True)

    if test:
        allocation_final = construct_allocation(allocation, buy_offers, sell_offers)
    else:
        auction_result = double_auction(buy_offers, sell_offers, allocation)
        allocation_final = construct_final_allocation(auction_result, buy_offers, sell_offers)

    # print(f"graph: {graph}")
    # print(f"allocation: {allocation}")
    # print(f"auction_result: {auction_result}")

    return allocation_final


