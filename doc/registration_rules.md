# Registration rules

## Reg message

### Minimal message

operation
hypernode:register

data
ip:port:pos_address

Sent from the dedicated collateral address (controller wallet) to itself

### Options

Optional: can give a different PoW address for rewards, so the collateral/controller wallet stays cold.

operation
hypernode:register

data
ip:port:pos_address,reward=bis_addr


## Unreg message

operation
hypernode:unregister

data
ip:port:pos_address

(Has to be sent from the same bis_addr as the register message to be valid)

## Auto unreg

Failsafe to avoid issues with lost keys and burned ips or old versions

- balance dropped (even temporarily) under the registered amount (indexed in local db)

- "too many" lying messages from "enough" other peers other some period

- no tx for NN rounds in a row

- version not in announced "allowable" posnet list (todo) 

Can be handled by the HN themselves, but a private contract can also send unreg messages to have the current state easily readable in the pow chain alone.

## One IP per HN

Register invalid if there is an already registered HN with that ip (whatever the port)

## One PoS address per HN

Register invalid if there is an already registered HN with that address
(User should unreg first, or create a new PoS address)

## One PoW address per HN

Register invalid if there is an already registered HN with that bis (collateral) address
(User should unreg first, or create a new PoW address and transfer)


## Collateral amount

real_value = math.floor(amount/10000)*10000

if real_value <= 0 : invalid
if real_value > 30000 : real_value = 30000

weight = real_value / 10000


# Temporary deactivation

- no tx for previous round (auto-reactivate by sending tx)

# Tools

TODO

## Registration Helper

Web page to check and give registration bis url

## HN Feed plugin

Plugin that listen to reg/unreg events and displays the feed as well as list of current HN and status


