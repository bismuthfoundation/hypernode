"""
Test debug week 41
"""

with open("rewards/week41_per_hn_address.local.csv") as f:
    rewards_redo = f.readlines()
rewards_redo = [line.strip().split(",") for line in rewards_redo]
rewards_redo = {a[0]: a[1:] for a in rewards_redo}
# print(rewards_redo)

with open("rewards/week41_per_hn_address.csv") as f:
    rewards = f.readlines()
rewards = [line.strip().split(",") for line in rewards]
rewards = {a[0]: a[1:] for a in rewards}
# print(rewards)

total = 0.0
for hn in rewards_redo:
    if hn not in rewards:
        r = rewards_redo[hn]
        print(f"{hn} not in original {r[1]} bis to {r[0]}")
        total += float(r[1])
print(total)

total = 0.0
for hn in rewards:
    if hn not in rewards_redo:
        r = rewards[hn]
        print(f"{hn} not in local {r[1]} bis to {r[0]}")
        total += float(r[1])
print(total)

"""
B9fRwdYtAZqpU6EMKDbjaojUfQwskJoTJQ not in original 93.08970374974103 bis to 51a6008ddb538484b9844662dbe21d7dcd2ca7e30e0b931d6b54e1ca
BRSGSJ7R1L4qUiEjrfa45i3z87jNfuWgmU not in original 41.55790345970582 bis to 6044c6f883edc967bdaaf925cc6ec2d16ec3c65e76ad52f2e58b8f98
B67S6s6uxGdUYRcMByrhEPwcfd6QM2zuwX not in original 33.24632276776466 bis to 455d58fabc17c64aa96854d60272aac044b8547632a7ba0e7545c2a6
BEGNTtQucSZzuae9Q6a5iBvJUfeZK39RJZ not in original 29.92169049098819 bis to 455d58fabc17c64aa96854d60272aac044b8547632a7ba0e7545c2a6
BPWuxpvZn5aPVh2hhgakKbU232TAPn9Amj not in original 29.92169049098819 bis to 455d58fabc17c64aa96854d60272aac044b8547632a7ba0e7545c2a6
B4ZioGhKed5AoSQiNfbSWGkpdyM8eZHSEz not in original 28.25937435259996 bis to 455d58fabc17c64aa96854d60272aac044b8547632a7ba0e7545c2a6
B8KHaxZq36CNxbi15Eeg3aDc7VzYEEJX8J not in original 28.25937435259996 bis to 455d58fabc17c64aa96854d60272aac044b8547632a7ba0e7545c2a6
BCLAz4oVwb8oMpfew87uQuYLXTRv5cvFeR not in original 28.25937435259996 bis to 05ff36bb190eb73a467dde487f40005edbc3327afea110b378f5cb63
B6SdVvLytJ4UETLS7zoLGBWQR9kbCN7bPE not in original 24.934742075823493 bis to 9463995e455116ed5e4969aac36e8f315eb1c4714ae076eaff6cded8
B9iB2wiUCwFdypncFstjV9kPoruzsF9BoX not in original 23.27242593743526 bis to 21469f889f1725a1682b80fe6f76ed59caf5d3f8c1111edc7680caf2
BPnNYqd3srsAbUobQJhmtXqFrTaWTam1Lp not in original 21.610109799047027 bis to 05ff36bb190eb73a467dde487f40005edbc3327afea110b378f5cb63
BNwuSMcADeYc3Fs1QmpRq7NKMVt2BmQjkS not in original 21.056004419584283 bis to 8af449d9fcdd439631e0e3be597743751d961cd8d63c62e3ba34ba55
B83G1phtHxneLc9DWxxF4Dr6y9ZiiDwTYe not in original 18.839582901733305 bis to 1c2be3e80e3208cb1ab279c6883bcda2ba809c9e0bda0e3d65e96e3c
BHTKNVywFuhmsdqiMnUHaVJy2cywFfs6eP not in original 11.63621296871763 bis to 8af449d9fcdd439631e0e3be597743751d961cd8d63c62e3ba34ba55
B9VCb8ek73Qo5tAqKBVhuogpFkv7w5mEeA not in original 8.311580691941165 bis to b920c5607e44a0ebd7ca4c6143007e56ff483bbd987775385d3bddef
442.17609281127
"""
