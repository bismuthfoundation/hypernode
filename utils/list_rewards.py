"""
Shows rewards for your hns

uses a "my_hns.csv" file, with ip,pos_address,label
"""

import argparse
import csv


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Helper")
    parser.add_argument(
        "-W", "--week", type=int, default=40, help="Week to check"
    )
    args = parser.parse_args()

    reward_file = "../stats/rewards/week{}_per_hn_address.csv".format(args.week)
    print("Using {}".format(reward_file))
    rewards = {}
    with open(reward_file) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            if line_count > 0:
                rewards[row[0]] = row[2]
            line_count +=1

    with open('my_hns.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            # print(row)
            pos, label = row[1], row[2]
            reward = rewards[pos] if pos in rewards else 'N/A'
            print(label, reward)
            line_count +=1
