# Pings

Simple ping client in Python 3 by using icmp packet via low level socket.

*Note: this client can only be used by **root** (or admin) user.*

## How to install

To install pings, simply:

```
$ pip install pings
```

or from source:

```
$ python setup.py install
```

## Getting started

Instantinate:

```
> import pings
> p = pings.Ping()
```

In case that you want to send simple ping:

```
> response = p.ping("google.com")
```

Then, pings it and returns a response object.
This resopnse object can be used for checking status (success or failed), messages and etc.

If you want to know status, you simply use `response.is_reached()`

```
> response.is_reached()  # If icmp packet successfully was reachecd, returns `True`.
```

If you want to know ping messages, you simply use `response.print_messages()`

```
> response.print_messages()

PING google.com (172.217.27.174): 55 data bytes
47 bytes from 172.217.27.174: icmp_seq=0 ttl=49 time=32.333 ms
--- google.com ping statistics ---
1 packets transmitted, 1 packets received, 0.0% packet loss
round-trip min/avg/max = 32.333/32.333/32.333 ms
```

## Other options

If you want print messages during executing on stdout, turns off `quiet` option (default: True).

```
> import pings
> p = pings.Ping(quiet=False)
> p.ping("google.com")

PING google.com (172.217.27.174): 55 data bytes
47 bytes from 172.217.27.174: icmp_seq=0 ttl=49 time=32.333 ms
--- google.com ping statistics ---
1 packets transmitted, 1 packets received, 0.0% packet loss
round-trip min/avg/max = 32.333/32.333/32.333 ms
```

If you want to ping multiple times, use option `times`.
Then, `is_reached` method is True in case that last packet was successfully sent to the destination.

```
> import pings
> p = pings.Ping(quiet=False)
> response = p.ping("google.com", times=3)

PING google.com (172.217.27.174): 55 data bytes
47 bytes from 172.217.27.174: icmp_seq=0 ttl=49 time=32.426 ms
47 bytes from 172.217.27.174: icmp_seq=1 ttl=49 time=32.160 ms
47 bytes from 172.217.27.174: icmp_seq=2 ttl=49 time=31.829 ms
--- google.com ping statistics ---
3 packets transmitted, 3 packets received, 0.0% packet loss
round-trip min/avg/max = 31.829/32.138/32.426 ms

> response.is_reached()
True
```
