# Client usage

See proto_client.py for an example of a very simple client (Communication starter only) using comhandler.  

## Import classes
```
import comhandler
import commands_pb2
```

## Define a handler instance

`handler = comhandler.Connection()`

When in a server context, we can pass a socket object directly:  
`handler = comhandler.Connection(socket=self.request)`

## Connect to a server

Client side, just call the connect method
`handler.connect(HOST, PORT)`

## Simple commands

Sending a simple command (one message, no argument)

> `handler.send_void(commands_pb2.Command.hello)`

## Other commands

Sending a command with a string param

> `handler.send_string(commands_pb2.Command.version,version)`

Sending a command with a int param

> `handler.send_int32(commands_pb2.Command.??,10)`


## Receiving a message

> `message = handler.get_message()`

## Helpers

- `handler.status()` A Json output of the internal comhandler vars. Including stats: a list of [start_timestamp,MSGSENT,MSGRECV,BYTSENT,BYTRECV]
- `message.__str__()` Where message is a protobuf instance (commands_pb2 class) : a readable version of the protobuf
