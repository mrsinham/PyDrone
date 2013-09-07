PyDrone
=======

PyDrone a simple monitoring tool written in Python based on the Tornado framework. It is capable of monitoring different
server of a single url by reading json files written in a specific format. It can simply say to you if the submitted url gives you a 200 http code.

The interface is based on bootstrap from Twitter, and is written for websocket. Be sure to have a modern browser that supports them.
PyDrone don't need a webserver, you just need to start it like that.

```
python PyDrone/Main.py --conf PyDrone/conf/configuration-sample.yaml
```

Todo
=====
- [ ] Make a setup.py file
- [ ] Send email when state change