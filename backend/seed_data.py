from models import Problem

PROBLEMS = [
    dict(
        title="Parking Lot",
        description=(
            "Design a parking lot with multiple floors, multiple spot sizes "
            "(compact, large, handicapped), ticketing on entry, fee calculation "
            "on exit, and support for concurrent entries. Handle a full lot and invalid tickets."
        ),
        difficulty="EASY", tags="oop,inventory,concurrency",
    ),
    dict(
        title="Elevator System",
        description=(
            "Design a multi-elevator system for a building serving external hall "
            "requests (up/down) and internal cabin requests. Optimize dispatch, "
            "handle concurrent requests, and support a maintenance/out-of-service mode."
        ),
        difficulty="MEDIUM", tags="scheduling,concurrency,state-machine",
    ),
    dict(
        title="Library Management System",
        description=(
            "Design a library system with books, members, borrowing, returning, "
            "reservations, fines for late returns, and limits on concurrent "
            "borrowed items per member. Handle an already-reserved or lost book."
        ),
        difficulty="EASY", tags="crud,inventory",
    ),
    dict(
        title="Vending Machine",
        description=(
            "Design a vending machine with inventory per slot, coin/note payment, "
            "change dispensing, and a simple state machine (idle, selecting, "
            "dispensing). Handle insufficient funds and an empty/invalid slot."
        ),
        difficulty="EASY", tags="state-machine",
    ),
    dict(
        title="Ride-Sharing Matching",
        description=(
            "Design a simplified ride matching service: riders request rides, "
            "drivers accept, fare is calculated by distance, and both parties can "
            "cancel. Handle no drivers available and a driver cancelling mid-ride."
        ),
        difficulty="HARD", tags="matching,concurrency",
    ),
]


def seed(db):
    if db.query(Problem).count() > 0:
        return
    for p in PROBLEMS:
        db.add(Problem(**p))
    db.commit()
