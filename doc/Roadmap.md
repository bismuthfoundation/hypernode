# Hypernodes Roadmap

These are just notes to give some insight into the direction we're going.

## 1.0 Release

Finalize 0.99 branch, marge in master branch.  

**State:** Near to completion

## Pruning nodes

Current Hypernodes keep all history from the start.   
Since the PoS chain does not have a currency, historical transactions are not critical and could be dropped for most of the nodes, except the ones willing to keep an historical archive.

Pruning nodes would allow to lower the disk space used, and accelerate some heavy requests.

Pruning could be done either by using a reference anchor block in the past, and delete up to there, or by keeping block info only, and pruning only the  transactions themselves.

**State:** Design

## Plugins

Would work on the same model as Tornado wallet plugins.  
Plugins will allow entities to operate additional services on top of regular PoS chain.  
These services could be rewarded. 

Plugins could trigger more test transactions with specific types and record service stats as well, plus provide extra client commands.

**State:** Plugin base architecture and code is in place and working. Now needs proper hooks, filters and doc.

## Transaction capping

Within the PoS layer, there is no currency, and transactions are for free.  
So, how do we prevent tx spamming?

- Transactions can be prioritized - tx from registered nodes first, or only -
- Transactions can be capped - quota per block per registered HN

That way, no one can spam the chain, transactions remain "for free" up to the quota, and the freezed collateral - on the main chain - acts as a guarantee fund for tx sending.

**State:** Already some kind of capping in the code, to be perfected and adapted to plugins transactions as well.

## Side chain framework

Instead of plugins on the existing hypernodes, provide guidance to easily operate alternate PoS chains, potentially dedicated to a single service.

Answers to scalability issues: a high tx demanding service could operate its own PoS chain, with the same mechanisms as the Hns, still backed by Bis collateral on the main chain.

**State:** Virtually done, would just need to run instances with the proper changes to the code and registration messages.   
Mainly a documentation issue.
