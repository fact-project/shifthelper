# Why using the shifthelper?

**Because it calls you, if there is work to be done**

During FACT observations, certain situations may arise, which call for fast human intervention. These include:

 * the weather might turn so bad, that the telescope needs to be parked.
 * the main control program, might throw an exception and stop.
 * a source flare was detected
 
So human intervention might also be something nice, in case of a flare :-D

In case human intervention is needed, the shifthelper calls a person and sends a Telegram message.
What exactly is checked can be seen [here](shifthelper/checks/webdim.py) and [here](shifthelper/checks/qla.py) (just the first 30 lines or so)
