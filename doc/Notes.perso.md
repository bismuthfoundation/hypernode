# 3rd party Utils

* Using SQLite studio for sqlite exploration and tables definition
* using pytest for help with tests
* pycharm as code editor/linter/debug

* Sphinx for auto documentation generation from docstrings within the code itself.

# Logging

Tornado log module with pretty printing is used.

log level

- INFO is used for verbose logging of regular messages
- WARNING is used for expected logic errors that are known to happen during execution, like a timeout.
- ERROR are only used for unexpected exceptions and should be reported to the devs.


# Personal notes

pos chain: no mining, no tx fee - marginal cost = 0
(chain can be pruned to reduce storage) -> don't recheck hash for blocks older than... who can be pruned. Keep the blocks, trash the tx.
no tx fee = service messages are free and can be mandatory in every block

no tx spam: only mn can send tx. only jurors can send specific messages.
spammy mn are visible and can be voted down. bad behavior penalizes the actor.
tx from a mn can also be throttled anyway, to avoid unvoluntary spam (bug?) 

No incentive in cheating: no bis, no direct advantage. Actions logged by everyone, will be seen and recorded.
rewards are NOT directly related to PoS forged blocks. 


Code for light tests only, can launch with only partial tests/checks, and update later on.
Can prepare a roadmap with the MN evolution

- firsts mn deployments
- relaxed checks, first data collection (goal: check for PoS stability, nothing breaks if it fails)
- first notation criterions, nodes evaluation
- bad actors penalization
- checks and notation improvements


Should "catching up" masternodes also verify the timeslots for each round (then they need the mn list for each round)
or can we skip this test? If we only ask masternodes (that are veryfied by each other) then no need?
Get full round in one go.
ask one and check signature on 3 others?
find consensus on N well noted mn, then fetch full data from any and recheck signature matches. 
keep a table with only signatures of previous rounds.
for sir 0, use whole prev_round hash instead of last blocks? (= hash of all the blocks hashes)


Raspberry pi image of node + HN
(not enough. orange pi2e : 2Gb, could do)


### TODO ###

Bootstrap. From h.b.live and/or bp12?


> plugin HN in node
- quicksync force false : !!Needs access to config object!!
- ok filter ec2
- ok add requirements from plugin to hn_check

Supervision / crontab

auto update

doc config python_executable


still some freeze when getting pow chain.
add a plugin to save the pow info from the node.
hn plugin, with ip filter included (+whitelist from successful regs)
- create data dir for hn list
- on status, create cache file for current round (a little in advance)
- keep N last files (or all? 1 per hour => clean)

config: short or full status into the logs?

check latest block timestamp(pow) and warns, suggests pow node not synced.

end of round: count how many times each peer was late (> 1 round late) to send a tx mentioning late nodes and slots #
(a late node is useless)


> Simulate connect_to , max , depending on hn list size and failure rates to estimate 
add this to config.json so we can adjust depending on the net state.


Message on the pos chain to announce recommended params and alert divergences?

"getconfig" message to void too far away HN

void a HN: message on the pow chain, from the HN private contract?
Or from a dedicated HN?
After each round: list of active, inactive, voided (sum = registered)
HN de facto have active and inactive. voided is done by private contract only. (can also serve as kill switch)
or pow chain, but only announce void/unvoid? 
>> or a list of voided only (both pow and pos), take last one into account.

Status: add total bytes sent/received since start within 'extra', as well as uptime (or start_timestamp, better)
Store those stats in a "stats" table or db, one stored status per round? could be helpful. 
Maybe also store the sorted peers status in that one. and in status or extended status.
So we can have a feeling on how many chain versions there are on the net.

Important: if DB empty, force to bootstrap.
Create a bootstrap at each round end with round - 2 for instance.
Incremental update in a cold database after a common ancestor check? 

> Store active_hns, slots and test_slots in pos_rounds 

Extra in status: add cpu% (app and system + ram / disk)

UFW for Python.

JWT for client/HN auth? - cf PyJWT, python micro services.

DONE hn_instance: opt config: what ip to listen on? (default all)

Since almost all code is async, maybe remove async_prefix we did not enforce everywhere, anyway.
If so, use the docstring to add "Async" prefix instead to all async functions.

Write a simplified async node, with only node related commands, no client commands?
Could serve as a base for a full async node later on, and will lighten the load on the hosting.
Most diff. thing: the sync state loop to clearly decompose.

DONE Reread docs and code, change occurrences of MN to HN (code ok)

HN need a full ledger - Enforce. Include historical pow data in tests?

Protocol: should we exchange current forger as part as current height to be safe?
> Not hard to do, not much overhead, would id splitting HNs before they even split.
Needs HF

peers agree with us : differentiate jurors (for forging) and all (for sync when late and not juror)
jurors only trust jurors.

Allow sync from jurors for non juror MNs (for current round)
same if juror missed a forged block: allow for late sync.

Auto-update/restart when code update or specific message (WIP - needs proper sync and bootstrap first) 

Check time > slot begin + delta not to send block too fast

Do not trigger "catching up" state if we are just at the beginning of a round: we could just be a few ms late.

When receiving a block, if last calculation of forger was not in that slot, refresh.

reference repo for bootstrapping.
update repo for auto updating (can be disabled)


=== Memo ===

WIP - Probly use static type hints? - MyPy => adding as we go


btc messages use:
- magic number to resync failed stream
- checksum in header
Both are easy to add with little overhead. reserve space for them in protobuf structure, even if not enforced at start.

=== DONE ===

DONE. See network number + checksum and b58encoding in btc https://en.bitcoin.it/wiki/File:PubKeyToAddr.png
Done  Do *not* send mempool if our mempool is empty? The other will send it to us anyway. And we will feed our also.
DONE at launch, check our mempool does not have stuck tx (way too old or already in ledger)
DONE *Important:* replace (or add) uniques 10 and forgers10 by round_uniques and round_forgers (metrics to decide the best current round chain)
done delete tx from mempool when catching up/digesting block
done digested block from miner: does not show tx, whereas there were. check.
done Important: see wallet server, add filehandler counts and such for debug/status.
DONE common.py: TODO: split this file into 2: one "utils" with the functions, and one "params" or "posconfig" with the chain parameters.
DONE Add "hello" to client commands.
DONE If same round than at least N peers, but peers get more valuable chain, get current round from one and fast check. if ok, digest (deep check) or replace.
DONE See mempool related Todo: real since and filter. 
DONE after tests, alleviate mempool verbosity
DONE Send a message at launch also (signal it's alive, and is a QoS metric... restarts too often = issue)
DONE HN Should send at least 1 or 2 message per round to say it's active, even if it has no test to be part of. (then he sends "No test for this round" to himself at begin and end of the round)

for past rounds, fetch one round in a single go.
get round total hash and # of sources from peers, take the biggest from our peers, fetch from him.
check on receive. if he lied, issue a tx and ignore him for a while.
add a message for that. 

TESTING heights message (client) to get heights of inbound + outbound peers
DONE Invalid reg if ip is not an ip / bis address / pos address
DONE close with error if windows: already an error message if not Posix.
DONE add a config.txt to override the config.py param
DONE hn_client, status: do not freeze but timeout after a few secs.
DONE hn_reg_feed : filter for 1 ip



