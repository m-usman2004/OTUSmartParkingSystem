import requests
from concurrent.futures import ThreadPoolExecutor
from collections import Counter

#central server endpoint for reserving a spot in Lot B
RESERVE_URL = "http://127.0.0.1:5000/api/lots/B/reserve"

#the spot all users will attempt to reserve
SPOT_ID = 1

#number of users attempting to reserve the same spot
NUM_USERS = 20

#simulate one user making a reservation request
def attempt_reservation(user_id):

    try:
        response = requests.post(
            RESERVE_URL,
            json={
                "spot_id": SPOT_ID,
                "user_name": f"User{user_id}"
            },
            timeout=10
        )

        return response.status_code

    except requests.RequestException:
        return "connection_error"


#run multiple reservation requests concurrently
def run_test():

    print(f"Simulating {NUM_USERS} users reserving the same spot...\n")

    #create threads to send requests concurrently
    with ThreadPoolExecutor(max_workers=NUM_USERS) as executor:
        results = list(
            executor.map(attempt_reservation, range(1, NUM_USERS + 1))
        )

    #count the HTTP responses
    counts = Counter(results)

    print("Test results:")
    print(f"Successful reservations (201): {counts[201]}")
    print(f"Conflicts (409): {counts[409]}")
    print(f"Other responses: {NUM_USERS - counts[201] - counts[409]}")

    #verify exactly one user successfully reserved the spot
    if counts[201] == 1 and counts[409] == NUM_USERS - 1:
        print("\nPASS: Only one user reserved the parking spot.")
    else:
        print("\nFAIL: Unexpected reservation results.")


if __name__ == "__main__":
    run_test()