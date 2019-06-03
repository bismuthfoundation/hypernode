"""
Test debug week 39
"""

with open("rewards/week39_per_hn_address.redo.csv") as f:
    rewards_redo = f.readlines()
rewards_redo = [line.strip().split(",") for line in rewards_redo]
rewards_redo = {a[0]: a[1:] for a in rewards_redo}
# print(rewards_redo)

with open("rewards/week39_per_hn_address.csv") as f:
    rewards = f.readlines()
rewards = [line.strip().split(",") for line in rewards]
rewards = {a[0]: a[1:] for a in rewards}
# print(rewards)

for hn in rewards_redo:
    if hn not in rewards:
        r = rewards_redo[hn]
        print(f"{hn} not in original {r[1]} bis to {r[0]}")

for hn in rewards:
    if hn not in rewards_redo:
        r = rewards[hn]
        print(f"{hn} not in redo {r[1]} bis to {r[0]}")

"""
B9DcaTwzzKCHovEMsPKibSqq6APcWJzaHu not in original 66.78867453971979 bis to 25125e9bb305fafd51ceb2858d355f77da99550b933ec0923cd156ff
B51G4b9E7qk21EJRYDVVaimbtvfrT4Lrds not in original 40.69243746790875 bis to 1a416bc8d96bf7263161f9f2c032daae5abbb5b8f8958920ed694dd8
BJKo6TPcAxcMapn8mKpgkPNU5u8nqsVGnK not in original 35.38472823296413 bis to 36c59c7780546179d7f80729e1ccc3932260b849bc519b2120074169
BMApWyFuYUaD84K6LjH9Y7Mb7tWPp8HDJu not in original 24.76930976307489 bis to e91b864b98fcaba034a8e9f63a21b23b96ec74fa38ce2154c1e0ac25
BA6jw1eByodLCHah2u43v9tQNwesHGHqNS not in original 22.705200616151984 bis to 25125e9bb305fafd51ceb2858d355f77da99550b933ec0923cd156ff
BDuBkpowzXsS67Kev1LtQeTvEu7W3JYwnA not in original 17.250055013570012 bis to d244e6e190969bae099cf994bd8d5d1cbfeb1e741092ad48313404b4
BAmvvhhNVptRzW8mEhfeGh1oSKNWxbMKzw not in original 10.173109366977188 bis to 8a92cbbb482843587e1ef46b4836ed2a916e25fc97889f6dc499a782
BGN5kQR2HbepxUPWCbshKd8VitRFBAjjpY not in original 6.487200176043424 bis to 9d9fc3f689fbf3bb0e5b2c9dd8e1bbd004c6bc7641ebbd3a548a33be
BPnNYqd3srsAbUobQJhmtXqFrTaWTam1Lp not in original 1.3269273087361548 bis to 05ff36bb190eb73a467dde487f40005edbc3327afea110b378f5cb63
"""
