from functools import reduce
import hashlib as hl
from collections import OrderedDict
import json

from hash_util import hash_string_256, hash_block
from block import Block

# initializing empty blockchain list
MINING_REWARD = 10
# We are the owner of this blockchain node, hence this is our identifier (e.g. for sending coins)
owner = "Kamil"
# Registered participants: Ourself + other people sending/ receiving coins
participants = {"Kamil"}


def load_data():
    global blockchain
    global open_transactions
    try:
        with open("blockchain.txt", mode="r") as f:
            file_content = f.readlines()
            global blockchain
            global open_transactions
            blockchain = json.loads(file_content[0][:-1])
            updated_blockchain = []
            for block in blockchain:
                converted_tx = [
                    OrderedDict(
                        [
                            ("sender", tx["sender"]),
                            ("recipient", tx["recipient"]),
                            ("amount", tx["amount"]),
                        ]
                    )
                    for tx in block["transactions"]
                ]

                updated_block = Block(
                    block["index"],
                    block["previous_hash"],
                    converted_tx,
                    block["proof"],
                    block["timestamp"],
                )
                updated_blockchain.append(updated_block)
            blockchain = updated_blockchain
            open_transactions = json.loads(file_content[1])
            updated_transactions = []
            for tx in open_transactions:
                updated_transaction = OrderedDict(
                    [
                        ("sender", tx["sender"]),
                        ("recipient", tx["recipient"]),
                        ("amount", tx["amount"]),
                    ]
                )
                updated_transactions.append(updated_transaction)
            open_transactions = updated_transactions
    except (IOError, IndexError):

        # Our starting block for the blockchain
        genesis_block = Block(0, "", [], 100, 0)
        # Initializing our (empty) blockchain list
        blockchain = [genesis_block]
        # Unhandled transactions
        open_transactions = []
    finally:
        print("Cleanup!")


load_data()


def save_data():
    try:
        with open("blockchain.txt", mode="w") as f:
            saveable_chain = [block.__dict__ for block in blockchain]
            f.write(json.dumps(saveable_chain))
            f.write("\n")
            f.write(json.dumps(open_transactions))
    except (IOError, IndexError):
        print("Saving failed!")


def get_last_blockchain_value():
    """Returns value of last blockchain element"""
    if len(blockchain) < 1:
        return None
    return blockchain[-1]


def valid_proof(transactions, last_hash, proof):
    """Validate a proof of work number and see if it solves the puzzle algorithm (two leading 0s)

    Arguments:
        :transactions: The transactions of the block for which the proof is created.
        :last_hash: The previous block's hash which will be stored in the current block.
        :proof: The proof number we're testing.
    """
    # Create a string with all the hash inputs
    guess = (str(transactions) + str(last_hash) + str(proof)).encode()
    # print('guess: ',guess)
    # Hash the string
    # IMPORTANT: This is NOT the same hash as will be stored in the previous_hash. It's a not a block's hash. It's only used for the proof-of-work algorithm.
    guess_hash = hash_string_256(guess)
    # Only a hash (which is based on the above inputs) which starts with two 0s is treated as valid
    # You could also require 10 leading 0s - this would take significantly longer (and this allows you to control the speed at which new blocks can be added)
    return guess_hash[0:2] == "00"


def proof_of_work():
    last_block = blockchain[-1]
    last_hash = hash_block(last_block)
    proof = 0
    while not valid_proof(open_transactions, last_hash, proof):
        proof += 1
    return proof


def get_balance(participant):
    tx_sender = [
        [tx["amount"] for tx in block.transactions if tx["sender"] == participant]
        for block in blockchain
    ]
    open_tx_sender = [
        tx["amount"] for tx in open_transactions if tx["sender"] == participant
    ]
    tx_sender.append(open_tx_sender)
    amount_sent = reduce(
        lambda tx_sum, tx_amt: tx_sum + sum(tx_amt) if len(tx_amt) > 0 else tx_sum + 0,
        tx_sender,
        0,
    )

    tx_recipient = [
        [tx["amount"] for tx in block.transactions if tx["recipient"] == participant]
        for block in blockchain
    ]
    amount_received = reduce(
        lambda tx_sum, tx_amt: tx_sum + sum(tx_amt) if len(tx_amt) > 0 else tx_sum + 0,
        tx_recipient,
        0,
    )

    # return the total balance
    return amount_received - amount_sent


def verify_transaction(transaction):
    sender_balance = get_balance(transaction["sender"])
    return sender_balance >= transaction["amount"]


def add_transaction(recipient, sender=owner, amount=1.0):
    """Append a new value as well as the last blockchain value to the blockchain

    Arguments:
        sender: the sender of the coins
        recipient: the recipient of the coins
        amount: the amount of coins sent with the transaction (default = 1.0)

    """
    # transaction = {
    #     "sender": sender,
    #     "recipient": recipient,
    #     "amount": amount
    # }
    transaction = OrderedDict(
        [("sender", sender), ("recipient", recipient), ("amount", amount)]
    )
    if verify_transaction(transaction):
        open_transactions.append(transaction)
        participants.add(sender)
        participants.add(recipient)
        save_data()
        return True
    return False


def mine_block():
    last_block = blockchain[-1]
    hashed_block = hash_block(last_block)
    proof = proof_of_work()

    # reward_transaction = {
    #     'sender': 'MINING',
    #     'recipient': owner,
    #     'amount': MINING_REWARD
    # }
    reward_transaction = OrderedDict(
        [("sender", "MINING"), ("recipient", owner), ("amount", MINING_REWARD)]
    )
    copied_transactions = open_transactions[:]
    copied_transactions.append(reward_transaction)
    block = Block(len(blockchain), hashed_block, copied_transactions, proof)
    blockchain.append(block)
    return True


def get_transaction_value():
    tx_recipient = input("Enter the recipient of the transaction: ")
    tx_amount = float(input("Enter transaction amount: "))
    return (tx_recipient, tx_amount)


def get_user_choice():
    return input("\nMake a choice: ")


def print_blockchain_blocks():
    for block in blockchain:
        print("Outputting block: ")
        print(block)
    else:
        print("-" * 20)


def verify_chain():
    """verify the current blockchain and return True if it's valid, False otherwise"""
    for (index, block) in enumerate(blockchain):
        if index == 0:
            continue
        if block.previous_hash != hash_block(blockchain[index - 1]):
            return False
        if not valid_proof(
            block.transactions[:-1], block.previous_hash, block.proof
        ):
            print("Proof of work is invalid")
            return False
    return True


def verify_transactions():
    return all([tx[verify_transaction] for tx in open_transactions])


waiting_for_input = True

while waiting_for_input:
    print("\nPlease choose: ")
    print("Enter new transaction value [1]")
    print("Mine new block [2]")
    print("Output blockchain blocks [3]")
    print("Output participants [4]")
    print("Check transactions validity [5]")
    print("quit [q]")
    user_choice = get_user_choice()
    if user_choice == "1":
        tx_data = get_transaction_value()
        recipient, amount = tx_data
        if add_transaction(recipient, amount=amount):
            print("Added transaction!")
        else:
            print("Transaction failed!")
        print(open_transactions)
    elif user_choice == "2":
        if mine_block():
            open_transactions = []
            save_data()
    elif user_choice == "3":
        print_blockchain_blocks()
    elif user_choice == "4":
        print(participants)
    elif user_choice == "5":
        if verify_transactions:
            print("All transactions are valid")
        else:
            print("There are invalid transactions!")
    elif user_choice == "q":
        waiting_for_input = False
    else:
        print("Invalid input!")
    if not verify_chain():
        print_blockchain_blocks()
        print("Invalid blockchain!")
        break
    print("Balance of {}: {:.2f}".format("Kamil", get_balance("Kamil")))

print("Done!")
